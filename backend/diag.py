import modal
import sys

image = modal.Image.debian_slim().pip_install("intuit-oauth")
app = modal.App("diag")

@app.function(image=image)
def check():
    from intuitlib.enums import Scopes
    print(f"Type: {type(Scopes.ACCOUNTING)}")
    if hasattr(Scopes.ACCOUNTING, "value"):
        print(f"Value: {Scopes.ACCOUNTING.value}")
    else:
        print(f"Value: {Scopes.ACCOUNTING}")

if __name__ == "__main__":
    import modal
    with modal.Retriever(app): # wait, this is still wrong but I'll use modal run
         pass
