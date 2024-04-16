import datetime
import os
from dataclasses import dataclass

import psycopg2
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Prompt:
    title: str
    prompt: str
    is_favorite: bool
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None


def setup_database():
    """
    Sets up the database by creating the 'prompts' table if it doesn't exist.
    """
    con = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            is_favorite BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    con.commit()
    return con, cur


def prompt_form(prompt=None):
    """
    Renders a form for user input with title, prompt, and favorite fields.

    Args:
        prompt (Prompt, optional): The default prompt to populate the form with. Defaults to None.

    Returns:
        Prompt: The user input as a Prompt object if the form is submitted successfully, None otherwise.
    """
    default = Prompt("", "", False) if prompt is None else prompt
    with st.form(key="prompt_form", clear_on_submit=True):
        title = st.text_input("Title", value=default.title)
        prompt = st.text_area("Prompt", height=200, value=default.prompt)
        is_favorite = st.checkbox("Favorite", value=default.is_favorite)

        submitted = st.form_submit_button("Submit")
        if submitted:
            if not title or not prompt:
                st.error("Title and prompt cannot be empty")
                return None
            else:
                return Prompt(title, prompt, is_favorite)


def toggle_favorite(con, cur, prompt_id, is_favorite):
    """
    Toggles the favorite status of a prompt.

    Args:
        con (connection): The database connection.
        cur (cursor): The database cursor.
        prompt_id (int): The ID of the prompt.
        is_favorite (bool): The current favorite status of the prompt.

    Returns:
        bool: The new favorite status of the prompt.
    """
    new_status = not is_favorite
    cur.execute(
        "UPDATE prompts SET is_favorite = %s WHERE id = %s", (new_status, prompt_id)
    )
    con.commit()
    return new_status


def display_prompts(
    con, cur, search_query=None, sort_order="DESC", filter_favorites=None
):
    """
    Display prompts based on search query, sort order, and filter favorites.

    Args:
        con (connection): The database connection.
        cur (cursor): The database cursor.
        search_query (str, optional): The search query to filter prompts. Defaults to None.
        sort_order (str, optional): The sort order for prompts. Defaults to "DESC".
        filter_favorites (bool, optional): The flag to filter favorite prompts. Defaults to None.

    Returns:
        None
    """
    sql_query = "SELECT * FROM prompts"
    where_clauses = []  # store all where clauses and combine later

    if filter_favorites:
        where_clauses.append(f"is_favorite = {filter_favorites}")

    if search_query:
        where_clauses.append("(title ILIKE %s OR prompt ILIKE %s)")

    if where_clauses:  # combine all where clauses
        sql_query += " WHERE " + " AND ".join(where_clauses)

    sql_query = sql_query + " ORDER BY created_at " + sort_order

    if search_query:
        cur.execute(sql_query, ("%" + search_query + "%", "%" + search_query + "%"))
    else:
        cur.execute(sql_query)

    prompts = cur.fetchall()

    for p in prompts:
        with st.expander(f"{p[1]}{' ★' if p[3] else ''}"):
            st.code(p[2])
            if filter_favorites == "FALSE":
                edit_clicked = st.button(
                    "Edit", key=f"edit-{p[0]}"
                )  # edit functionality
                with st.form(f"form-{p[0]}"):
                    new_title = st.text_input("Title", value=p[1])
                    new_prompt = st.text_area("Prompt", value=p[2], height=200)
                    new_is_favorite = st.checkbox("Favorite", value=p[3])
                    submitted = st.form_submit_button("Submit Changes")
                    if submitted and edit_clicked:
                        cur.execute(
                            "UPDATE prompts SET title = %s, prompt = %s, is_favorite = %s WHERE id = %s",
                            (new_title, new_prompt, new_is_favorite, p[0]),
                        )
                        con.commit()
                        st.rerun()

            if st.button(
                "Toggle Favorite", key=f"fav-{p[0]}"
            ):  # toggle favorite functionality
                toggle_favorite(con, cur, p[0], p[3])
                st.rerun()

            if st.button("Delete", key=p[0]):  # delete functionality
                cur.execute("DELETE FROM prompts WHERE id = %s", (p[0],))
                con.commit()
                st.rerun()


if __name__ == "__main__":
    st.title("Prompt Store!")
    st.subheader(
        "A simple app to store and retrieve prompts for your everyday GPT needs!"
    )
    st.divider()

    # setup database
    con, cur = setup_database()

    # sort radio buttons for ascending or descending order
    sort_order = st.radio("Sort by", ["Newest", "Oldest"], index=1)
    sort_order_sql = "DESC" if sort_order == "Newest" else "ASC"

    # filter by favorites checkbox
    show_favorites_only = st.checkbox("Show only favorites")
    show_favs = "TRUE" if show_favorites_only else None

    # search bar
    search_query = st.text_input("Search your prompts!")
    search_button = st.button("Search")

    new_prompt = prompt_form()
    if new_prompt:
        try:
            cur.execute(
                "INSERT INTO prompts (title, prompt, is_favorite) VALUES (%s, %s, %s)",
                (new_prompt.title, new_prompt.prompt, new_prompt.is_favorite),
            )
            con.commit()
            st.success("Prompt added successfully!")
        except psycopg2.Error as e:
            st.error(f"Database error: {e}")

    st.divider()
    st.header("Your Prompts")
    if search_button or search_query:
        display_prompts(
            con, cur, search_query, sort_order_sql, filter_favorites=show_favs
        )
    else:
        display_prompts(con, cur, sort_order=sort_order_sql, filter_favorites=show_favs)

    con.close()
