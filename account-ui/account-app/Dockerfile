FROM node:22-alpine AS build
WORKDIR /app
COPY ./public ./public
COPY ./src ./src
COPY index.html package.json package-lock.json tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts .
RUN npm install
RUN npm run build
FROM nginx:alpine AS production
COPY --from=build /app/dist/ /usr/share/nginx/html/user/
COPY ./src /usr/share/nginx/html/src
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx.sh /
RUN chmod +x /nginx.sh
EXPOSE 4042
CMD /nginx.sh
