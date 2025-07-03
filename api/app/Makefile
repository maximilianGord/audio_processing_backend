# Use TAB characters for indentation (not spaces!)
PG_IMAGE := postgres:15
PG_NAME := my-postgres
PG_USER := mytestuser
PG_PASSWORD := mypassword
PG_DB := mysuperdb
PG_PORT := 5432

postgres-up:  ## Start PostgreSQL container
	docker run -d \
		--name $(PG_NAME) \
		-p $(PG_PORT):5432 \
		-v postgres_data:/var/lib/postgresql/data \
		-e POSTGRES_USER=$(PG_USER) \
		-e POSTGRES_PASSWORD=$(PG_PASSWORD) \
		-e POSTGRES_DB=$(PG_DB) \
		$(PG_IMAGE)

postgres-down:  ## Stop and remove container (keeps data)
	docker stop $(PG_NAME) && docker rm $(PG_NAME)