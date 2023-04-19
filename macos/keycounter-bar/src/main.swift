//
//  main.swift
//  keycounter-bar
//
//  Created by Raúl Caro Pastorino on 19/4/23.
//
import Foundation

let socketPath = "/var/run/keycounter.socket"

// Creamos la estructura de la dirección del socket Unix
var socketAddress = sockaddr_un()
socketAddress.sun_family = sa_family_t(AF_UNIX)
strncpy(&socketAddress.sun_path.0, socketPath, MemoryLayout.size(ofValue: socketAddress.sun_path))

// Creamos el socket
let socketFileDescriptor = socket(AF_UNIX, SOCK_STREAM, 0)
guard socketFileDescriptor != -1 else {
    fatalError("Error al crear el socket")
}

// Conectamos el socket al servidor
let connectResult = withUnsafePointer(to: &socketAddress) {
    $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
        connect(socketFileDescriptor, $0, socklen_t(MemoryLayout.size(ofValue: socketAddress)))
    }
}
guard connectResult != -1 else {
    fatalError("Error al conectarse al socket")
}

// Creamos el buffer para recibir los datos
let bufferSize = 1024
var buffer = [UInt8](repeating: 0, count: bufferSize)

// Mantenemos el socket abierto y recibimos los datos
while true {
    let bytesRead = read(socketFileDescriptor, &buffer, bufferSize)
    guard bytesRead != -1 else {
        fatalError("Error al leer del socket")
    }
    
    // Convertimos los datos en una cadena
    //let jsonString = String(bytes: buffer, encoding: .utf8)!
    //print("Datos recibidos:", jsonString)
    
    do {
        let data = Data(bytes: buffer, count: bytesRead)
        if let dict = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] {
            // Utilizar el diccionario recibido aquí "dict"
            //print(dict)
            
            print(dict)
            
            if let streakDict = dict["streak"] as? [String: Any],
               let pulsationAverage = streakDict["pulsation_average"] as? Int {
                let avg = pulsationAverage
                print(avg)
                //setMenuItemValue(value: avg ?? "N/A")
                //setMenuItemValue(value: "N/A")
            }
            
            
        } else {
            print("Error al convertir la cadena JSON en un diccionario")
        }
    } catch let error as NSError {
        print("Error al convertir la cadena JSON en un diccionario: \(error.localizedDescription)")
    }

    
    
    
    // Limpiamos el buffer
    buffer = [UInt8](repeating: 0, count: bufferSize)
}

// Cerramos el socket (esto nunca se ejecutará en este ejemplo)
close(socketFileDescriptor)
