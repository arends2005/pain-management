<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# 

---

# im on main and I need to create a new branch to test a new feature

To create a new branch and test a new feature, follow these steps:

1. **Ensure you're on the `main` branch**:

```bash
git checkout main
```

2. **Pull the latest changes from `main` to ensure it's up to date**:

```bash
git pull origin main
```

3. **Create a new branch for your feature**:
Replace `feature-name` with a descriptive name for your feature.

```bash
git checkout -b feature-name
```

4. **Start working on the new branch**:
Make your changes, add files, and commit as needed:

```bash
git add .
git commit -m "Description of the changes made"
```

5. **Push the branch to the remote repository (if needed)**:

```bash
git push origin feature-name
```


You can now work on your feature independently without affecting the `main` branch. Once your work is complete and tested, you can merge it back into `main`.

