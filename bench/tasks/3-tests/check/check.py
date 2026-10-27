import sys, unittest, pathlib, re; d=sys.argv[1]; sys.path.insert(0,d)
assert "def slugify" in pathlib.Path(d,"slug.py").read_text() and "max_len=60" in pathlib.Path(d,"slug.py").read_text()
t=pathlib.Path(d,"test_slug.py").read_text(); assert len(re.findall(r"def test_",t))>=5
r=unittest.TextTestRunner(verbosity=0).run(unittest.defaultTestLoader.discover(d,"test_slug.py"))
assert r.wasSuccessful() and r.testsRun>=5
