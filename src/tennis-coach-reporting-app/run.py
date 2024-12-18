from app import create_app

app = create_app()

if __name__ == '__main__':
    # Flask backend runs on port 5000
    # React will run on port 3000
    app.run(host='localhost', port=8000, debug=True)