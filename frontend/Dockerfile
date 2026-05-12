FROM node:22-alpine

WORKDIR /app

ARG NEXT_PUBLIC_API_URL=https://ai-infra-backend-41844796013.europe-central2.run.app
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY package*.json ./

RUN npm ci

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
