"""Builder for Grade Reports."""
import os
import shutil
import subprocess
from glob import glob
from itertools import groupby

from jinja2 import Environment, FileSystemLoader
try:
    from bibtexparser.bwriter import BibTexWriter
    from bibtexparser.bibdatabase import BibDatabase
    HAVE_BIBTEX_PARSER = True
except ImportError:
    HAVE_BIBTEX_PARSER = False

try:
    import numpy as np
except ImportError:
    np = None

from regolith.tools import all_docs_from_collection, date_to_float, \
    date_to_rfc822, rfc822now, gets, month_and_year
from regolith.sorters import doc_date_key, ene_date_key, category_val, \
    level_val, id_key, date_key, position_key

LATEX_OPTS = ['-halt-on-error', '-file-line-error']

def latex_safe(s):
    return s.replace('&', '\&').replace('$', '\$').replace('#', '\#')


class GradeReportBuilder(object):

    btype = 'grades'

    def __init__(self, rc):
        self.rc = rc
        self.bldir = os.path.join(rc.builddir, self.btype)
        self.env = Environment(loader=FileSystemLoader([
                    'templates',
                    os.path.join(os.path.dirname(__file__), 'templates'),
                    ]))
        self.construct_global_ctx()
        if HAVE_BIBTEX_PARSER:
            self.bibdb = BibDatabase()
            self.bibwriter = BibTexWriter()

    def construct_global_ctx(self):
        self.gtx = gtx = {}
        rc = self.rc
        gtx['len'] = len
        gtx['True'] = True
        gtx['False'] = False
        gtx['None'] = None
        gtx['sorted'] = sorted
        gtx['groupby'] = groupby
        gtx['gets'] = gets
        gtx['date_key'] = date_key
        gtx['doc_date_key'] = doc_date_key
        gtx['level_val'] = level_val
        gtx['category_val'] = category_val
        gtx['rfc822now'] = rfc822now
        gtx['date_to_rfc822'] = date_to_rfc822
        gtx['month_and_year'] = month_and_year
        gtx['latex_safe'] = latex_safe
        gtx['all_docs_from_collection'] = all_docs_from_collection
        gtx['grades'] = list(all_docs_from_collection(rc.client, 'grades'))
        gtx['courses'] = list(all_docs_from_collection(rc.client, 'courses'))
        gtx['assignments'] = list(all_docs_from_collection(rc.client,
                                                           'assignments'))

    def render(self, tname, fname, **kwargs):
        template = self.env.get_template(tname)
        ctx = dict(self.gtx)
        ctx.update(kwargs)
        ctx['rc'] = ctx.get('rc', self.rc)
        ctx['static'] = ctx.get('static',
                               os.path.relpath('static', os.path.dirname(fname)))
        ctx['root'] = ctx.get('root', os.path.relpath('/', os.path.dirname(fname)))
        result = template.render(ctx)
        with open(os.path.join(self.bldir, fname), 'wt') as f:
            f.write(result)

    def build(self):
        os.makedirs(self.bldir, exist_ok=True)
        self.latex()
        self.pdf()
        self.clean()

    def latex(self):
        rc = self.rc
        for course in courses:
            stats = self.makestats(course)
            for student_id in course['students']:
                self.render('gradereport.tex', p['_id'] + '.tex', p=p,
                            title=p.get('name', ''), stats=stats)
                self.pdf(p)

    def pdf(self, p):
        """Compiles latex files to PDF"""
        base = p['_id']
        self.run(['latex'] + LATEX_OPTS + [base + '.tex'])
        self.run(['bibtex'] + [base + '.aux'])
        self.run(['latex'] + LATEX_OPTS + [base + '.tex'])
        self.run(['latex'] + LATEX_OPTS + [base + '.tex'])
        self.run(['dvipdf', base])

    def run(self, cmd):
        subprocess.run(cmd, cwd=self.bldir, check=True)

    def clean(self):
        postfixes = ['*.dvi', '*.toc', '*.aux', '*.out', '*.log', '*.bbl',
                     '*.blg', '*.log', '*.spl', '*~', '*.spl', '*.run.xml',
                     '*-blx.bib']
        to_rm = []
        for pst in postfixes:
            to_rm += glob(os.path.join(self.bldir, pst))
        for f in set(to_rm):
            os.remove(f)

    def makestats(self, course):
        """Returns a dictionary of statistics for a course whose keys are
        the assignments and whose values are a (mean-problem, std-problem,
        mean-total, std-total) tuple.
        """
        scores = {}
        course_id = course['_id']
        for grade in self.gtx['grades']:
            if grade['course'] != course_id:
                 continue
            assignment_id = grade['assignment']
            if assignment_id not in scores:
                scores[assignment_id] = []
            scores[assignment_id].append(grade['scores'])
        stats = {}
        for assignment_id, data in scores.items():
            stats[assignment_id] = (np.mean(data, axis=0),
                                    np.std(data, axis=0),
                                    np.mean(np.sum(data, axis=1)),
                                    np.std(np.sum(data, axis=1)))
        return stats