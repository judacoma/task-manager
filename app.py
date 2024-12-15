import streamlit as st
import json
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration with SQLAlchemy
DATABASE_URL = "sqlite:///tasks.db"

Base = declarative_base()

# Task Model
class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    completed = Column(Boolean, default=False)

# Database connection
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def load_tasks(db):
    return db.query(Task).all()

def save_task(db, title, description):
    db_task = Task(title=title, description=description, completed=False)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def mark_completed(db, task_id):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.completed = True
        db.commit()
        db.refresh(task)
    return task

def delete_task(db, task_id):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
    return task

def export_to_json(db):
    tasks = load_tasks(db)
    tasks_json = [{"title": task.title, "description": task.description, "completed": task.completed} for task in tasks]
    
    with open("exported_tasks.json", "w") as file:
        json.dump(tasks_json, file, indent=4)

    with open("exported_tasks.json", "rb") as file:
        return file.read()

def import_from_json(uploaded_file, db):
    try:
        tasks = json.load(uploaded_file)
        for task in tasks:
            save_task(db, task['title'], task['description'])
        st.success("Tasks imported successfully from JSON.")
    except json.JSONDecodeError:
        st.error("Invalid JSON file. Please upload a valid tasks file.")

def main():
    st.title("TASK MANAGER")

    db = next(get_db())

    st.subheader("Add a New Task")

    if "task_title" not in st.session_state:
        st.session_state.task_title = ""
    if "task_description" not in st.session_state:
        st.session_state.task_description = ""

    title = st.text_input("Task Title", value=st.session_state.task_title)
    description = st.text_area("Task Description", value=st.session_state.task_description)

    if st.button("Add Task"):
        if title.strip():
            save_task(db, title, description)
            st.session_state.task_title = ""
            st.session_state.task_description = ""
            st.rerun()  # Reemplaza experimental_rerun() con rerun()
            st.success("Task added successfully!")
        else:
            st.warning("Title is required to add a task.")

    st.subheader("Export Tasks to JSON")
    json_data = None
    if st.button("Export to JSON"):
        json_data = export_to_json(db)
        st.success("Tasks exported to JSON!")

    if json_data:
        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name="exported_tasks.json",
            mime="application/json"
        )

    st.subheader("Import Tasks from JSON")
    uploaded_file = st.file_uploader("Choose a JSON file", type="json")
    if uploaded_file is not None:
        import_from_json(uploaded_file, db)

    st.subheader("Your Tasks")
    tasks = load_tasks(db)
    if tasks:
        for task in tasks:
            col1, col2, col3 = st.columns([6, 2, 2])
            with col1:
                st.markdown(f"<h4>{task.title}</h4>", unsafe_allow_html=True)
                st.write(task.description)
                status_color = "green" if task.completed else "red"
                st.markdown(f"<p style='color: {status_color};'>Status: {'Completed' if task.completed else 'Pending'}</p>", unsafe_allow_html=True)
            with col2:
                if not task.completed:
                    if st.button("Mark Completed", key=f"complete_{task.id}"):
                        mark_completed(db, task.id)
                        st.rerun()  # Reemplaza experimental_rerun() con rerun()
            with col3:
                if task.completed:
                    if st.button("Delete", key=f"delete_{task.id}"):
                        delete_task(db, task.id)
                        st.rerun()  # Reemplaza experimental_rerun() con rerun()
    else:
        st.info("No tasks available.")

if __name__ == "__main__":
    main()
