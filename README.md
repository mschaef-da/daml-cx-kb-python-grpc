
This is a sample program intended to illustrate basic interaction with
a Canton ledger via direct Python calls to the Ledger API. It is
composed of a simple Daml model, code to manage a local sandbox
running that model, and a Python program that can execute various
commands against that sandbox instance.

## Setting up Your Development Environment

1. Install the following dependencies:

   | Tool                                                                                | Minimum Version |
   |-------------------------------------------------------------------------------------|-----------------|
   | [direnv](https://direnv.net/#basic-installation)                                    | 2.34.0          |
   | [yq](https://github.com/mikefarah/yq)                                               | 4.25.3          |
   | [GNU Make](https://www.gnu.org/software/make/)                                      | 3.81            |
   | [Open JDK 17](https://www.azul.com/downloads/?version=java-17-lts&package=jdk#zulu) | 17              |

2. Ensure Python 3.13 or newer is installed with `venv`
   - Although `venv` should be installed by default, on some systems
     (e.g. Ubuntu) it may be required to install it explicitly.
3. Then `make build` will build the Daml code and install all required
   dependencies for the Python project

## Running Commands

Once the project is built, start a ledger with the command
`make start-ledger`. You should see output similar to this:

```
scripts/start-ledger.sh ./asset-model/.daml/dist/asset-model-0.0.1.dar
INFO: Started Canton ledger (PID: 91298) with log output in log/
INFO: Waiting 30 seconds for startup...
INFO: ...Ledger running
```

Once the ledger is running, the Canton logs are visible under the
`log/` directory, and the Python program can be invoked via the `run`
script. In the spirit of `git`, it offers a range of subcommands for
various functions it offers:


```
~/daml-cx-kb-python-grpc $ ./run
Available subcommands:
   allocate-party
   archive-asset
   give-asset
   issue-asset
   ledger-end
   list-contracts
   list-local-parties
   list-packages
   list-parties
   list-updates
   repeatedly
   stream-updates
   version
```

An example of a simple interaction:

### Allocate two parties: `alice` and `bob`:

```
$ ./run allocate-party alice
party_details {
  party: "alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26"
  display_name: "alice"
  is_local: true
  local_metadata {
    resource_version: "0"
  }
}

n= 1

$ ./run allocate-party bob
party_details {
  party: "bob::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26"
  display_name: "bob"
  is_local: true
  local_metadata {
    resource_version: "0"
  }
}

n= 1
```

### Alice Issues an Asset and Inspects the Result

```
$ ./run issue-asset alice widget

$ ./run list-updates alice
===== Transaction ofs: 16, command_id: bfebd6f5c2c845c1b06356e4fd12e9c8, wfid:
  === EVENT:  created Main:Asset 00cc9fc2e39a3c1b714fe0f098d3316b5f05fa9df36989b6d3f87d21c3b4fd37e8ca10122075714ad478b8f1b16939df7eab16c64cf483852e50ffa03de9051af93657edbe
       {'issuer': Party(party='alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26'),
        'name': 'widget',
        'owner': Party(party='alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26')}
```

### Alice Transfers the Asset to Bob and Looks at the Transaction Log

```
$ ./run give-asset 00cc9fc2e39a3c1b714fe0f098d3316b5f05fa9df36989b6d3f87d21c3b4fd37e8ca10122075714ad478b8f1b16939df7eab16c64cf483852e50ffa03de9051af93657edbe alice bob

$ ./run list-updates alice
===== Transaction ofs: 16, command_id: bfebd6f5c2c845c1b06356e4fd12e9c8, wfid:
  === EVENT:  created Main:Asset 00cc9fc2e39a3c1b714fe0f098d3316b5f05fa9df36989b6d3f87d21c3b4fd37e8ca10122075714ad478b8f1b16939df7eab16c64cf483852e50ffa03de9051af93657edbe
       {'issuer': Party(party='alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26'),
        'name': 'widget',
        'owner': Party(party='alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26')}


===== Transaction ofs: 21, command_id: 4fef22681cca407cb64f26a5a48c0ec7, wfid:
  === EVENT:  archived Main:Asset 00cc9fc2e39a3c1b714fe0f098d3316b5f05fa9df36989b6d3f87d21c3b4fd37e8ca10122075714ad478b8f1b16939df7eab16c64cf483852e50ffa03de9051af93657edbe
  === EVENT:  created Main:Asset 00bd3b6653ec749cf979f71921cb199b4f7e740819613ddffec29e300396664cacca101220ca162b15550237839923d40ccc58e548c0d5a63b2d0b45a7e392bd86b86631d6
       {'issuer': Party(party='alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26'),
        'name': 'widget',
        'owner': Party(party='bob::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26')}
```

A couple observations on the transaction log:

* The initial transaction (offset 16) is shown in the log in addition
  to the transfer transaction (offset 21).
* The transfer transaction is composed of two parts - the archival of
  the contract indicating Alice owns the widget and the creation of
  the contract indicating Bob owns the same.

### Bob Observes he can See the Asset

```
$ ./run list-updates bob
===== Transaction ofs: 21, command_id: , wfid:
  === EVENT:  created Main:Asset 00bd3b6653ec749cf979f71921cb199b4f7e740819613ddffec29e300396664cacca101220ca162b15550237839923d40ccc58e548c0d5a63b2d0b45a7e392bd86b86631d6
       {'issuer': Party(party='alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26'),
        'name': 'widget',
        'owner': Party(party='bob::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26')}
```

Note that Bob sees the same transfer transaction (offset 21) as
Alice. (Which makes sense, since this is the transaction in which he
gained ownership of the asset.)

### Bob Attempts to Archive the Asset

```
$ ./run archive-asset 00bd3b6653ec749cf979f71921cb199b4f7e740819613ddffec29e300396664cacca101220ca162b15550237839923d40ccc58e548c0d5a63b2d0b45a7e392bd86b86631d6 bob

   ... Elided...

grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
	status = StatusCode.INVALID_ARGUMENT
	details = "DAML_AUTHORIZATION_ERROR(8,abb374b9): Interpretation error: Error: node NodeId(0) (82e970dbd4338688f1b402266645f0a708522cccc9ba85aee529a1dd8a76323a:Main:Asset) requires authorizers alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26, but only bob::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26 were given"
	debug_error_string = "UNKNOWN:Error received from peer  {grpc_message:"DAML_AUTHORIZATION_ERROR(8,abb374b9): Interpretation error: Error: node NodeId(0) (82e970dbd4338688f1b402266645f0a708522cccc9ba85aee529a1dd8a76323a:Main:Asset) requires authorizers alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26, but only bob::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26 were given", grpc_status:3}"
```

Bob does not have rights to do this.

### Alice Archives the Asset Successfully and Inspects the Result

```
$ ./run archive-asset 00bd3b6653ec749cf979f71921cb199b4f7e740819613ddffec29e300396664cacca101220ca162b15550237839923d40ccc58e548c0d5a63b2d0b45a7e392bd86b86631d6 alice

$ ./run list-updates alice
===== Transaction ofs: 16, command_id: bfebd6f5c2c845c1b06356e4fd12e9c8, wfid:
  === EVENT:  created Main:Asset 00cc9fc2e39a3c1b714fe0f098d3316b5f05fa9df36989b6d3f87d21c3b4fd37e8ca10122075714ad478b8f1b16939df7eab16c64cf483852e50ffa03de9051af93657edbe
       {'issuer': Party(party='alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26'),
        'name': 'widget',
        'owner': Party(party='alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26')}


===== Transaction ofs: 21, command_id: 4fef22681cca407cb64f26a5a48c0ec7, wfid:
  === EVENT:  archived Main:Asset 00cc9fc2e39a3c1b714fe0f098d3316b5f05fa9df36989b6d3f87d21c3b4fd37e8ca10122075714ad478b8f1b16939df7eab16c64cf483852e50ffa03de9051af93657edbe
  === EVENT:  created Main:Asset 00bd3b6653ec749cf979f71921cb199b4f7e740819613ddffec29e300396664cacca101220ca162b15550237839923d40ccc58e548c0d5a63b2d0b45a7e392bd86b86631d6
       {'issuer': Party(party='alice::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26'),
        'name': 'widget',
        'owner': Party(party='bob::122005d3eb878afd11dd6b6356f0b0cd3743412022dfe495b69f2a9bae307698ae26')}


===== Transaction ofs: 25, command_id: d4192db34f5c41ac9e4a04defd2ea34e, wfid:
  === EVENT:  archived Main:Asset 00bd3b6653ec749cf979f71921cb199b4f7e740819613ddffec29e300396664cacca101220ca162b15550237839923d40ccc58e548c0d5a63b2d0b45a7e392bd86b86631d6
```
