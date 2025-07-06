// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "OpenDict",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "OpenDict",
            targets: ["OpenDict"]
        )
    ],
    targets: [
        .executableTarget(
            name: "OpenDict",
            path: "HelloWorldApp"
        )
    ]
) 