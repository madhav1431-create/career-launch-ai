"""Small, deterministic practice projects for skills in the learning roadmap."""


_PROJECTS = {
    "python": (
        "Write a Python script that reads a sales CSV and summarizes sales by category.",
        "A runnable script, a sample CSV, and a summary CSV with totals by category.",
        "Run the script on four rows and compare each category total with a hand calculation.",
    ),
    "r": (
        "Use R to chart and summarize weekly sales for two stores.",
        "An R script, a grouped box plot, and a table with each store's median.",
        "Check both medians by hand on a small sample and rerun with the input rows shuffled.",
    ),
    "javascript": (
        "Build a JavaScript task list that can add, filter, and complete items.",
        "A working page and a short list of the interactions it supports.",
        "Add two tasks, complete one, then verify each filter and blank-input handling.",
    ),
    "typescript": (
        "Write a TypeScript function that validates order records before totaling them.",
        "Typed source code, three sample records, and a summary that flags rejected rows.",
        "Compile in strict mode and test valid, missing, and wrong-type fields.",
    ),
    "html": (
        "Create a one-page HTML sign-up form with semantic sections and labeled fields.",
        "An HTML page with a heading, form, validation message, and accessible labels.",
        "Use only the keyboard to fill the form and check that each field has a visible label.",
    ),
    "css": (
        "Use CSS to turn a three-card product grid into a single-column mobile layout.",
        "A stylesheet and screenshots at phone and desktop widths.",
        "Check at 375px and 1280px that cards stay readable without horizontal scrolling.",
    ),
    "machine learning": (
        "Train a simple classifier on a small labeled dataset and compare it with a majority baseline.",
        "A reproducible notebook with the split, baseline, model, and confusion matrix.",
        "Evaluate both methods on the same held-out rows and explain one model error.",
    ),
    "deep learning": (
        "Train a small neural network to classify grayscale digits on a subset of a labeled dataset.",
        "Training and validation curves, test accuracy, and three misclassified examples.",
        "Keep test examples out of training, then compare training and test accuracy for overfitting.",
    ),
    "statistics": (
        "Compare two groups in a public dataset and estimate the uncertainty in the difference.",
        "A chart, the group sizes, the difference in means, and a short interpretation of its confidence interval.",
        "Check the means on a tiny sample by hand and confirm that your interpretation matches the interval.",
    ),
    "numpy": (
        "Use NumPy to normalize each column of a small matrix of sensor readings.",
        "A script showing the original matrix, the normalized matrix, and column summaries.",
        "Check that each nonconstant column has mean near zero and standard deviation near one.",
    ),
    "pandas": (
        "Use Pandas to clean a transactions CSV and summarize revenue by month.",
        "A notebook, a cleaned CSV, and a monthly revenue table.",
        "Reconcile the monthly totals with the cleaned source and explain how duplicates and missing values were handled.",
    ),
    "scikit-learn": (
        "Build a scikit-learn pipeline that imputes missing values and classifies customer churn.",
        "A fitted pipeline, a held-out score, and a table of prediction errors.",
        "Fit preprocessing on the training set and compare held-out accuracy with a majority baseline.",
    ),
    "opencv": (
        "Use OpenCV to count light-colored objects in a simple photo with thresholding and contours.",
        "An annotated image with numbered contours and a script that prints the count.",
        "Compare the counts with a manual count on three photos taken against different backgrounds.",
    ),
    "nlp": (
        "Train a bag-of-words classifier to sort short support messages into two categories.",
        "A notebook with tokenization, the category results, and examples of wrong predictions.",
        "Hold out several labeled messages and test how typos or unseen words affect predictions.",
    ),
    "computer vision": (
        "Compare two simple image features on a small two-class image dataset.",
        "A reproducible notebook, a confusion matrix for each feature, and sample errors.",
        "Hold out photos from a different scene and compare the errors with your validation results.",
    ),
    "reinforcement learning": (
        "Train a tabular agent to reach a goal in a small grid with one obstacle.",
        "The learned policy as arrows on the grid and a graph of rewards across episodes.",
        "Start the agent from several cells and compare its average path length with a random policy.",
    ),
    "transformers": (
        "Run a pretrained text Transformer on ten short reviews and compare predictions with your own labels.",
        "A table with expected labels, model labels, confidence scores, and two failure examples.",
        "Check the ten rows by hand and see whether adding a negation changes predictions as expected.",
    ),
    "sql": (
        "Write a SQL query that joins customers and orders and summarizes revenue by customer.",
        "A schema, sample inserts, and a query with one result row per customer.",
        "Check the totals by hand for two customers, including one with no orders.",
    ),
    "mongodb": (
        "Use MongoDB to summarize order totals per customer with an aggregation pipeline.",
        "Sample JSON documents, the aggregation stages, and the result table.",
        "Insert a second order for an existing customer and confirm only that customer's total changes.",
    ),
    "spark": (
        "Use Spark to clean and group a local CSV of trip records by day.",
        "A local Spark job, a small input file, and daily totals written as Parquet.",
        "Compare row counts and daily totals with a hand-labeled subset and rerun on another input file.",
    ),
    "hadoop": (
        "Run a small word-count MapReduce job in local mode on two text files.",
        "The input files, a runnable job, and a sorted word-count table.",
        "Choose three words in advance and compare the output counts against the files by hand.",
    ),
    "airflow": (
        "Build an Airflow DAG that reads a CSV, checks the row count, and writes a daily summary.",
        "A DAG file, a sample input, and a dated output file.",
        "Test a valid input and an empty input, then rerun one date and check for duplicate outputs.",
    ),
    "kafka": (
        "Publish sample order events to a local Kafka topic and consume them into a file.",
        "A producer, a consumer, and an event log showing the order IDs read.",
        "Restart the consumer and verify which offsets are resumed and whether any events are duplicated.",
    ),
    "redis": (
        "Add a Redis cache to a small endpoint that reads sample records from a file.",
        "An endpoint with a short cache expiration and logs for cache hits and misses.",
        "Make two identical requests and one after expiration. Confirm the hit and miss sequence.",
    ),
    "elasticsearch": (
        "Index a handful of support articles and create a search for their titles and tags.",
        "An index mapping, sample documents, and a list of queries with their top results.",
        "Check the top results for a known title, a shared keyword, and a query that should return nothing.",
    ),
    "docker": (
        "Package a small web app in Docker and document how to start it.",
        "A Dockerfile, a built image, and a README with the build and run commands.",
        "Start a clean container from the image and verify that its health endpoint returns HTTP 200.",
    ),
    "kubernetes": (
        "Deploy a small containerized web app to a local Kubernetes cluster with a health probe.",
        "Deployment and Service manifests plus a successful rollout record.",
        "Delete a pod, confirm it is replaced, and verify that the Service returns a successful response.",
    ),
    "git": (
        "Use Git to make a small change on a branch, review the diff, and merge it.",
        "A repository with a short commit history and a README explaining the branch workflow.",
        "Inspect the merge with git log and confirm the change is present in the target branch.",
    ),
    "github": (
        "Open a pull request for a small change in a practice GitHub repository.",
        "A pull request with a clear summary, a focused diff, and steps for reviewers to verify it.",
        "Check that the changed files match the description and that the verification steps work from a fresh checkout.",
    ),
    "ci/cd": (
        "Create a CI workflow that installs a tiny app and runs its tests on each push.",
        "A workflow file and screenshots of one failing run and one successful run.",
        "Intentionally break one assertion, confirm the check turns red, and verify it passes after the fix.",
    ),
    "terraform": (
        "Use Terraform to manage one local file as a small infrastructure exercise.",
        "A Terraform configuration, a README with apply and destroy steps, and a saved plan summary.",
        "Apply twice and confirm the second plan has no changes, then verify destroy removes the file.",
    ),
    "mlops": (
        "Create a command that trains a small model and saves its data version, metrics, and model artifact.",
        "A training script and two run records with the model paths and recorded metrics.",
        "Rerun with the same data and seed, then compare the saved metrics and load the artifact for one prediction.",
    ),
    "data structures": (
        "Build a small FIFO task queue and track completed IDs in a set.",
        "A working queue with enqueue and dequeue operations and a test file.",
        "Check arrival order, duplicate IDs, and behavior when the queue is empty.",
    ),
    "algorithms": (
        "Implement linear and binary search and count comparisons on sorted lists of increasing size.",
        "Two implementations, test inputs, and a comparison-count table.",
        "Verify both agree on found, missing, and boundary cases, then explain the growth in comparisons.",
    ),
    "system design": (
        "Design a small URL-shortener service for a fixed traffic target.",
        "A component diagram, a request flow, and a short note explaining one bottleneck and trade-off.",
        "Trace a create and a redirect through the diagram, then explain what happens if the data store goes offline.",
    ),
    "microservices": (
        "Build two local services where one fetches product details from the other.",
        "Two runnable endpoints and a short runbook with normal and failure examples.",
        "Stop the downstream service and confirm the caller returns a bounded timeout and useful error.",
    ),
    "agile": (
        "Plan a one-week sprint for a tiny product feature using three user stories.",
        "A backlog with acceptance criteria, a sprint goal, and a short review of what was completed.",
        "Ask someone to verify a completed story against its acceptance criteria and update the backlog from their feedback.",
    ),
    "excel": (
        "Use Excel to clean a sales sheet and summarize sales by month with a PivotTable.",
        "A workbook with the source table, a PivotTable, and one chart.",
        "Reconcile the grand total with the source and add a row to confirm the refreshed pivot includes it.",
    ),
    "power bi": (
        "Build a one-page Power BI dashboard from a small sales CSV.",
        "A .pbix file with order count, total sales, a trend chart, and a short written takeaway.",
        "Filter to one month and reconcile both metrics with the CSV. Check that the takeaway matches the data shown.",
    ),
    "tableau": (
        "Build a Tableau dashboard that shows monthly sales and lets users filter by region.",
        "A workbook with a trend chart, a regional filter, and a short takeaway.",
        "Select one region and compare two plotted monthly totals with the source data.",
    ),
}


# Related tools can exercise the same concept while producing tool-specific work.
_SHARED_PROJECTS = (
    (
        {"java": "Java", "c++": "C++", "c#": "C#", "scala": "Scala", "go": "Go"},
        (
            "Write a {tool} command-line program that counts words in a text file.",
            "A runnable program and a frequency table for a small sample file.",
            "Compare results with hand counts and test empty input, uppercase words, and punctuation.",
        ),
    ),
    (
        {"react": "React", "angular": "Angular", "vue": "Vue"},
        (
            "Build a {tool} component that adds, filters, and completes tasks.",
            "A working component with a form, a filtered list, and an empty state.",
            "Add two tasks, complete one, and check each filter and blank-input validation.",
        ),
    ),
    (
        {"node.js": "in Node.js", "flask": "in Flask", "fastapi": "in FastAPI", "django": "in Django",
         "api": "as an API", "rest api": "as a REST API"},
        (
            "Build a small catalog {tool} that lists items and fetches one by ID.",
            "A runnable service and example requests for the list route and item route.",
            "Confirm an existing item returns HTTP 200, a missing item returns 404, and the list uses the expected JSON shape.",
        ),
    ),
    (
        {"tensorflow": "TensorFlow", "pytorch": "PyTorch", "keras": "Keras"},
        (
            "Train a small {tool} classifier on a subset of labeled digit images.",
            "A training script, a saved checkpoint, and an accuracy report on held-out images.",
            "Load the checkpoint in a fresh process and confirm its predictions agree with the original report.",
        ),
    ),
    (
        {"mysql": "MySQL", "postgresql": "PostgreSQL"},
        (
            "Use {tool} to create an orders table and index its customer ID column.",
            "A schema, a sample data loader, and query plans from before and after adding the index.",
            "Check the query results stay the same and use the plan to explain whether the index is used.",
        ),
    ),
    (
        {"aws": "AWS", "azure": "Azure", "gcp": "Google Cloud"},
        (
            "Practice an object-storage backup for {tool} in a sandbox or local emulator.",
            "A sample file, upload and restore instructions, and a recorded checksum.",
            "Restore to a fresh folder, compare the checksum, and verify that private files cannot be read without access.",
        ),
    ),
    (
        {"linux": "Linux", "unix": "Unix"},
        (
            "Write a {tool} shell script that counts error codes in a sample log file.",
            "A shell script, sample logs, and a sorted count of errors by code.",
            "Compare the counts with a hand tally and test an empty file and an unreadable path.",
        ),
    ),
)

for tool_names, project in _SHARED_PROJECTS:
    _PROJECTS.update({
        skill: tuple(text.format(tool=tool) for text in project)
        for skill, tool in tool_names.items()
    })


def practice_project(skill):
    """Return a project, artifact, and check for a roadmap skill."""
    project, output, check = _PROJECTS.get(skill, (
        f"Use one documented feature of {skill} in a small example with two inputs.",
        "The example, its two inputs, and a short README with the steps and expected results.",
        "Follow the README from scratch and compare the results for both inputs with your predictions.",
    ))
    return {"project": project, "output": output, "check": check}
