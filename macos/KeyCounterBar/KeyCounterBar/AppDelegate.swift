import Cocoa
import Foundation
import NIO
import NIOFoundationCompat
import NIOTransportServices
import Dispatch

let timeRefreshRate: TimeInterval = 2.0

// Define structs for decoding JSON data
struct DataJSON: Decodable {
    let session: Session
    let streak: Streak
}

struct Session: Decodable {
    let pulsations_total: Int
}

struct Streak: Decodable {
    let pulsations_current: Int
    let pulsation_average: Int
}

// Define DataHandler
final class DataHandler: ChannelInboundHandler {
    typealias InboundIn = ByteBuffer
    var data: DataJSON?
    
    func channelRead(context: ChannelHandlerContext, data: NIOAny) {
        var byteBuffer = self.unwrapInboundIn(data)
        let data = byteBuffer.readData(length: byteBuffer.readableBytes)
        let decoder = JSONDecoder()
        if let data = data, let message = try? decoder.decode(DataJSON.self, from: data) {
            self.data = message
            
            // Close connection after reading data
            context.close(promise: nil)
        }
    }
}

// Define leerSocket function
func leerSocket(group: NIOTSEventLoopGroup) -> EventLoopFuture<DataJSON> {
    let bootstrap = NIOTSConnectionBootstrap(group: group)
    let dataHandler = DataHandler()

    let channelFuture = bootstrap.connect(unixDomainSocketPath: "/var/run/keycounter.socket")

    let _ = channelFuture.whenSuccess { channel in
        _ = channel.pipeline.addHandler(dataHandler)
    }

    return channelFuture.flatMap { channel in
        channel.closeFuture.flatMapThrowing { _ in
            guard let data = dataHandler.data else {
                // Handle error appropriately
                throw SocketError.noDataReceived
            }
            return data
        }
    }
}

struct SocketError: Error {
    var reason: String

    static let noDataReceived = SocketError(reason: "No data was received from the socket.")
}

// AppDelegate class
@NSApplicationMain
class AppDelegate: NSObject, NSApplicationDelegate {
    let statusBar = NSStatusBar.system
    var statusBarItem: NSStatusItem!
  
    let group = NIOTSEventLoopGroup()

    // beginSocketReadingLoop definition
    func beginSocketReadingLoop() {
        leerSocket(group: group).whenComplete { result in
            switch result {
            case .success(let dataJson):
                let text = "\(dataJson.streak.pulsations_current) / \(dataJson.streak.pulsation_average)AVG / \(dataJson.session.pulsations_total)T"
                
                DispatchQueue.main.async {
                    self.statusBarItem.button?.title = text
                }
                
            case .failure(let error):
                print("Encountered error: \(error)")
            }

            // call beginSocketReadingLoop with a delay of two seconds to create a loop
            DispatchQueue.global().asyncAfter(deadline: .now() + 1.0) {
                self.beginSocketReadingLoop()
            }
        }
    }

    func applicationDidFinishLaunching(_ aNotification: Notification) {
        statusBarItem = statusBar.statusItem(withLength: NSStatusItem.variableLength)
        beginSocketReadingLoop() // begin the loop of reading socket
    }

    func applicationWillTerminate(_ aNotification: Notification) {
        do {
            try group.syncShutdownGracefully()
        } catch {
            print("Error shutting down: \(error)")
        }
    }
}
