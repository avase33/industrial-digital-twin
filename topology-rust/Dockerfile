FROM rust:1.79-slim AS build
WORKDIR /app
COPY Cargo.toml ./
COPY src ./src
RUN cargo build --release --bin idt-topology

FROM debian:bookworm-slim
COPY --from=build /app/target/release/idt-topology /usr/local/bin/idt-topology
ENV TOPOLOGY_ADDR=0.0.0.0:8092
EXPOSE 8092
CMD ["idt-topology"]
