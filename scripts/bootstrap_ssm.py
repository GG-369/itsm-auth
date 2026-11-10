import argparse, secrets, boto3
def main(stage,region):
    ssm=boto3.client("ssm",region_name=region); name=f"/itsm-auth/{stage}/jwt-secret"
    try: ssm.get_parameter(Name=name,WithDecryption=True); print(f"{name} ya existe; no se modifica.")
    except ssm.exceptions.ParameterNotFound:
        ssm.put_parameter(Name=name,Value=secrets.token_urlsafe(48),Type="SecureString",Description="JWT signing secret")
        print(f"Creado {name} como SecureString.")
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--stage",default="dev"); p.add_argument("--region",default="us-east-1"); a=p.parse_args(); main(a.stage,a.region)
