from fastapi import APIRouter

router = APIRouter(tags='Accounts')


@router.post('auth/register')
async def create_user():
    ...