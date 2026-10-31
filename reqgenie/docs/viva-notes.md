# Viva and presentation notes

Short answers your team can use if the mam asks questions.

**What is ReqGenie in one line?**
A tool that turns client requirements into user stories, acceptance criteria and UML diagrams, and updates only the affected parts when requirements change.

**Where is the "adaptive" part?**
`app/diffing.py` and `engine.update()`. A new version of the text is compared with the old one. Unchanged requirements keep their stories and IDs. Only edited or new requirements are regenerated. Removed requirements are listed in the Changes tab. Every version is stored, so nothing is lost.

**Which Agile ideas does it use?**
User stories, acceptance criteria, MoSCoW prioritisation, Scrum sprints, and handling change during development.

**Does it use real AI?**
The current analyser uses language rules (patterns for actors, modal verbs such as "can" and "must", and a verb list) so it runs offline and gives repeatable results. The analyser is one function (`analyse_requirement`), so an LLM can replace it without touching the rest of the system.

**How is MoSCoW priority decided?**
By the words in the sentence: "must", "shall", "need" give Must. "should" gives Should. "could", "may", "optional" give Could. "won't", "later" give Won't. No keyword gives Should.

**How are the diagrams made?**
`app/diagrams.py` writes Mermaid text from the stories. The browser draws it. GitHub also renders Mermaid inside the exported Markdown.

**How does it connect to our lab work?**
Git and pull requests (Experiment 5), Docker (Experiment 6), JIRA board and sprints (Experiment 3), Kanban (Experiment 4), and the E-Commerce case study (Experiment 1) as the sample input.

**What are the limits?**
Rule-based analysis works best on clear sentences. Vague or very long notes give generic stories. We plan an LLM analyser as future work.

**How do we demo it in 2 minutes?**
1. Open the app, click Load sample, click Generate.
2. Show the stories and the three diagrams.
3. Paste `samples/ecommerce_changed.txt`, click Save as new version.
4. Show the Changes tab (kept, edited, added, removed) and pick Version 1 from the dropdown.
5. Download the JIRA CSV.
