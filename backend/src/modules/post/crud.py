from fastcrud import FastCRUD

from .models import Post

crud_posts: FastCRUD = FastCRUD(Post)
