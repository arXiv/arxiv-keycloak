FROM node:22-alpine AS build
WORKDIR /app
COPY ./public ./public
COPY ./src ./src
COPY index.html package.json package-lock.json tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts .
RUN npm install
RUN npm run build
FROM nginx:alpine AS production
COPY --from=build /app/dist/ /usr/share/nginx/html/user-account/
COPY ./src /usr/share/nginx/html/src
COPY ./nginx/default.conf ./nginx/nginx.conf ./nginx/template-source /etc/nginx/conf.d/
COPY nginx.sh /
RUN chmod +x /nginx.sh
EXPOSE $PORT
CMD /nginx.sh
