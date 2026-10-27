import sys, pathlib; d=pathlib.Path(sys.argv[1]); sys.path.insert(0,str(d))
src="".join(f.read_text() for f in d.glob("*.py"))
assert "get_usr" not in src and src.count("get_user")==5, src.count("get_user")
import api, cli; assert api.handler(7)=={"id":7}
