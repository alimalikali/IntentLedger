"""Create the synthetic IntentLedger Git fixture with fixed identities/timestamps."""
import json,os,subprocess,sys
from pathlib import Path
P=Path(sys.argv[1] if len(sys.argv)>1 else ".intentledger/demo").resolve()
def git(*a,env=None): subprocess.run(["git","-C",P,*a],check=True,capture_output=True,env=env)
def write(name,text): (P/name).parent.mkdir(parents=True,exist_ok=True); (P/name).write_text(text)
def commit(message,stamp):
    env={**os.environ,"GIT_AUTHOR_NAME":"IntentLedger Fixture","GIT_AUTHOR_EMAIL":"fixture@invalid.local","GIT_COMMITTER_NAME":"IntentLedger Fixture","GIT_COMMITTER_EMAIL":"fixture@invalid.local","GIT_AUTHOR_DATE":stamp,"GIT_COMMITTER_DATE":stamp}; git("add",".",env=env); git("commit","-m",message,env=env)
if P.exists(): subprocess.run(["rm","-rf",P],check=True)
P.mkdir(parents=True); git("init","-b","main")
write("package.json",'{"name":"synthetic-payment-app","private":true}')
write("tsconfig.json",'{"compilerOptions":{"baseUrl":".","paths":{"@app/*":["src/*"]}}}')
write("docs/adr-001-direct.md","# Direct SDK access\nStatus: Superseded\n\nServices may call `payment-sdk` directly.\n")
write("src/adapters/payment.ts","import sdk from 'payment-sdk';\nexport const charge = sdk.charge;\n")
write("src/services/checkout.ts","import { charge } from '../adapters/payment';\nexport const checkout = charge;\n")
write("src/services/legacy/settle.ts","import sdk from 'payment-sdk';\nexport const settle = sdk.charge;\n")
commit("initial direct SDK guidance","2024-01-01T00:00:00Z")
write("docs/adr-002-adapter.md","# Payment adapter boundary\nStatus: Accepted\n\nAll services must use `src/adapters/payment.ts`. Legacy settlement is excepted.\n")
commit("accept payment adapter decision","2024-02-01T00:00:00Z")
write("src/services/refund.ts","import sdk from 'payment-sdk';\nexport const refund = sdk.refund;\n")
commit("introduce direct SDK regression","2024-03-01T00:00:00Z")
# unmerged proposal branch
main=subprocess.run(["git","-C",P,"rev-parse","main"],text=True,capture_output=True,check=True).stdout.strip(); git("checkout","-b","proposal","HEAD~1"); write("docs/proposal.md","Maybe services should access the SDK directly again.\n"); commit("unaccepted proposal","2024-04-01T00:00:00Z"); git("checkout","main")
write("fixture-refs.json",json.dumps({"main":main,"base":"main~1","head":"main","proposal":"proposal"},indent=2))
print(P)
