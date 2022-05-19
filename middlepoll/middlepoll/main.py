import os
from typing import Union

import click
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

load_dotenv()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

SECRET_KEY = os.getenv("secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


def get_sample_token(username):
    # TODO remove this to test
    token = jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)
    return token


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data


@app.get("/")
def read_root():
    return {"health": "ok"}


@app.get("/me/", response_model=TokenData)
async def read_users_me(current_user: TokenData = Depends(get_current_user)):
    return current_user


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@click.command()
@click.option("--port", type=int, default=8000)
@click.option("--host", default="0.0.0.0")
def main(port: int, host: str):
    """
    Run the server.
    """
    import uvicorn

    print("sample token", get_sample_token("test"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
