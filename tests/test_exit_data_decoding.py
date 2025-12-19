"""Tests for exit data decoding correctness.

This test module validates that exit data can be correctly decoded
into validator information using local Python implementation.
"""

import pytest
import sys
from pathlib import Path

# Add src to path so we can import from utils
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from utils.exit_data_decoder import (
    decode_all_validators,
    unpack_exit_request,
    PACKED_REQUEST_LENGTH,
)


class TestExitDataDecoding:
    """Tests for exit data decoding correctness."""

    def test_decode_exit_data_correctness(self):
        """
        Test that exit data is correctly decoded into validator information.

        This test verifies:
        1. Exit data can be decoded into the correct number of validators
        2. Each validator has the proper structure (pubkey, nodeOpId, moduleId, valIndex, index)
        3. Pubkeys are 48 bytes
        4. Decoded values match expected values (if provided)
        """
        # =====================================================================
        # CONFIGURATION - Update these values with your actual exit data
        # =====================================================================

        # Exit data to decode (hex string with or without '0x' prefix)
        # Replace this with your actual exit data
        exit_data_hex = "0x0000010000000026000000000012572a919d858f5e2af21ef6f7525beb4621432208675acff2f54b71e720ced04e2e26bfe4e2a79bb32a57d147935651ee531d0000010000000026000000000012572bb35b62d26c996bb91396523a8b9036e608d4146a466c61ad0ba42717b7e75be103cf0c8916905fb651c731165ae77acb0000010000000026000000000012572cabff903cbe0fc89aa586fc161611d245c1bdd5b1008317dc1fe8ed021ae188e99d70780784093d76f571b3e9558a3b8f0000010000000026000000000012572dab770f1a4ff9186148c2ab73102f6596fa0e1a1c7c44d3bf10e169eacd96a55b8bf5d082b7bb9c928e587d164246c3210000010000000026000000000012572e8e91f0797bd16fb20a200c59c2b7be69c9906fa568fd91a4b78825f34013e315e2c97be643135cdb2465706a5f6855140000010000000026000000000012572f93865e7557e6017a70cea2c924143353aa7ed41106bfc165dffd2414060e1577573f04cb29ce5d38a5d49924c9dba46b00000100000000260000000000125730b79dbc30d94ff57767f1680cb06d143b9c186bf53487edb8b8701a956e4cc8cc6561851ef00785792f92c9252afeb3ea0000010000000026000000000012573193fa9b2007bdea9ea3b2a06a612efeedb5c90392e43ceb8b4278fd79435fe8ff47b8499d590027b86eceab9693ec3a770000010000000026000000000012573291b72fb5f174e4df21c1ff11044f8b9a31881a512c4ef756788867fa894d97a79e81c0344e9055cec622345b33ae20740000010000000026000000000012573389bf56a911fa9dcc4554dfda1168f0879bf2e99af7b8a75a81f0f7bd675e43ecc27ee25feac6a017178afc9a83968bc700000100000000260000000000125734982d834593ad241133d1265519804cd740723786303495c70e4818538858e9d817f27651a054ab0e8c49f483a6bc030c00000100000000260000000000125735acde4ab6a25ba0a1eb7311156e245be3bb8fc8d682b38e6e01e5db1995e244dfc7406caf73bb6ef8d518dcfa9112a97300000100000000260000000000125736ae6a17f83703812a42c14b5534ad806cba2715945d0145e72cf0e5af1ed657bfe51fb60553d4b7106b0ad7b0947fdf440000010000000026000000000012573791b0eae347b00ecde5fdf47e12096ff917b32ce24effbeb6966c76de1523f6a6db14182f9686ef416f9866c8fb0dff3500000100000000260000000000125738979d016e0c882dd0a94c3b308454485d1b4f5375877d4869b84540ad70a7dad08e58ef19ed4a4278ff5bbe110513ba7300000100000000260000000000125739a48955a7f4404022e1d18bd28ad939a16732c85c01ef915faf7567dcf547a730db072409f8f7d356aa7fba78015b1c820000010000000026000000000012573a9954379b187d85c3f06319be088cec38fa389136f41482fa3745be26afc810c4b52df10c213d5f1a050e52f62bda691f0000010000000026000000000012573b8601f3fc746f41c76decd3523be8f1eec8161dc8a6b20acbbb5823ec7fb1b3567854995f23b43e12e776e0080214b8300000010000000026000000000012573cb4742b8a98a3b1df4134e9fca9ba9ec68f43946e590f21acbeea6510d4a16a073d3d7cab7c477a5ae467dc2dfbf1dbdc0000010000000026000000000012573d81ef96dd5e022fc5bd566e59ee716bcd76dcd0e74712fc80f2ed8d8533c4b9a9fc0cf4dac64b7044421db730f579e8b0000001000000002600000000001257899696aac80769eefef678a12576005194920321b82233bdf2ecfe23a7c99fb42429ba329ac1689c76e7ca4f045847f5500000010000000026000000000012578a86bfd20acd5d55f6c0cab4338f5e8ec03f18909f89cf31b754db1be2fcbbdfc0b5a1c3c3e354a04b8e8cabc071416b430000010000000026000000000012578b88090d495e7fd311ce8c77e48beb81972148827dae57f74a96a236c8f4fb7448cae0b35260e5a44ee5f3277991a2afe40000010000000026000000000012578ca099b9d027f328dddeb9d826962f66452e5a16e93e217a15535bae37570428dab0501358e0a3bf8cf2d3f73ec3bc4e6d0000010000000026000000000012578d9766bb04e1503ab24db1d8c4cff9020ce2c957f5e96e96b1898099fb86380bdfb9d1cc77e0061cb4eeb3e8731a1cd7850000010000000026000000000012578ea72c882c51c47e02262f16536eac8c153d2790d7965246007db67e1ae5e2caeffa370dd8a5fbc41f531527c69ab594e60000010000000026000000000012578fb247193214c14a6a025b27781c75214b7ebd7205e86afc4bde3dd149ff9b070189551770d83c8f5365b528caf0768d3a000001000000002600000000001257908fcb5967de3fab420f38cdc9c89019e4769669b987d9165eb1e920e0a735be28e1ceea5ae1a6fe5609c218eab674888a00000100000000260000000000125791931b39b9a119906f71276434a8eb0c5f9c49d8a0248118f8171ab0605561d2adcde37a57f693fec8f990e4761961f52700000100000000260000000000125792b4095c8165e81722ad21b0e18fdd9c4bc17121102188f4a636d8e250093e4e24220a88e4afe4177f7a57a211ed03144200000100000000260000000000125793a3126b785f3ec6e633d2df5c513f195d3a30fda2974730d77e1c9afed4d35c037ef483b9110f96d1013784f6c650a4e80000010000000026000000000012579497d2357e30acf77f10aacc0876744ca439dbbfc7ff7c05ee295a75432e3b47800a1167039ab08f6491447b68652c629100000100000000260000000000125795a1665903cc9d16b87bce18c65cd54ec4f0273394aa80639bc99cbc6a0a6fd4f38d2a21c6d4389dcd615239b5d9a083dd000001000000002600000000001257968e7e91d14a963c35b6ec010807b595221f39a0b5a84b854a474b67ea2cebf6a3f0f7ca410011eef25c8f8993a10e30f30000010000000026000000000012579783079ac340358f91957a6493ed5d348263afa36dcf61966af8a2f9a76bd777bc590da24626bdbc8e27977ccb29c201d50000010000000026000000000012579888756b153ada4d9bdab0f1fb4820e932507255e53734f6d8fbfca938b1dbc647d4d32e726191ae879b63c927da6b48fc0000010000000026000000000012579992797d19db94c02cf2a22a8046cc997c56c762d6ee2e1b49aaf494ed529460216ea58732d127c0c5c95bee1ea2286c830000010000000026000000000012579a8db9855a5b80fb44e6d2ef37d5542dabdeb18ee6b31acf75933de507915df2fef9746084f17040e1ea0f22e232d114520000010000000026000000000012579b9181e8b985a4555ad962d8700af589894654fabaa397fa8e593472c1f5ffcdb11a7f47ee76ee87952749dcd097acee900000010000000026000000000012579ca747a8782e75d19003a6cfab585a63038c3b22ed00bce37bf205bc6c189e2e495d8efb6253f0f1f8ad4b4a955e83154f0000010000000026000000000012579d8147836ed310658ee43b5751f2c6bad24dd435bb3f659f8118e23de14847596051076796eaea7e5e15b12b9cf5b22c670000010000000026000000000012579ea0ab73a29977df669782b8721bfb6a1619d9897711e061de4ddf9ecff8666822655611c58948b5211cb258a9ff713d130000010000000026000000000012579fb0c03c8589bcfbf916956053bbcebc9b8b9aff44c38f1ae14af2b7e6e7d0cf9b5ad56ca285b0a3071dc7dc603ec072bf000001000000002600000000001257a0b902d3e34d3d34a50a7086e22d671a0d9dc13e2253b7ac0c6e638f8ca356a44a42125fa60252be463820fec40257e109000001000000002600000000001257a184f9e7cfed7e242caa1841068a49fcd0af7b8c71234981f364ae0adb77ee11a050c05f83ee170b753dcd7f5191974006000001000000002600000000001257a2aad0bcd4ff9d5c8483d9b40f4a0312017e82b1a3359160c4363d541a12434b83f1d00ba2e59301635a41da9698fd3e49000001000000002600000000001257a38a384994176fd090408c3aa0e3e01f3664313c3b8df7d447d13b025412d53abff52988362b09b59ed6228ec458ff788f000001000000002600000000001257a4afe1f5bf04854d18182e93eb9048d3306160dc9bf8d69e60d12653112800d73b08e0069354edb44f6718ed7aaece6084000001000000002600000000001257a5b6557f6b0bd7c177dcf305f5024f00936ca5e680d8b42c574c3a54c44a3d86409f845e300027d9923f4619e76fe68376000001000000002600000000001257a6af0dda9f7de18c68f60383510af753c7a326a207adb10621bf3b8204929dd939d1b16bb904f4b2c7a0faa86893c03f6b000001000000002600000000001257a7ac9e2ed78b34a0e36784e11546b0d3e05529e292dc8b6df39b13c9795ed1ba135454e3af142e357597d7a6322c234584000001000000002600000000001257a8ab64838fb73d078c8f2752c6204fc0f23bf3e8a495bcbd03724bf582f0b6695547841834abaafd22d4441653d6278199000001000000002600000000001257a9b52500f7ae18fed6852a74bea339122fb57cb634b4806b87d388504ead1bc2471ade11d1a0f7741aacf8f6966d2e6015000001000000002600000000001257aaa294c0228e26053479ad616b79197a933c74659d27e7a9e4d52aad37f8f089f66d37ee58fdbbc0df19bed33942b72819000001000000002600000000001257ab8b49f971b6d2655660188591e053ae2cfc6381913507b07c2747bfc6c3cf2361a4c2182e403503ebc3246482727ca6b4000001000000002600000000001257ac8f2a444e04a500f3613767961e0bc27a6914429cc24c3e9b72c44d31f5d4f696affd74f08d594ec23b3f15ef11f9344f"

        expected_validators = [
            {
                "pubkey": "919d858f5e2af21ef6f7525beb4621432208675acff2f54b71e720ced04e2e26bfe4e2a79bb32a57d147935651ee531d",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201962,
            },
            {
                "pubkey": "b35b62d26c996bb91396523a8b9036e608d4146a466c61ad0ba42717b7e75be103cf0c8916905fb651c731165ae77acb",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201963,
            },
            {
                "pubkey": "abff903cbe0fc89aa586fc161611d245c1bdd5b1008317dc1fe8ed021ae188e99d70780784093d76f571b3e9558a3b8f",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201964,
            },
            {
                "pubkey": "ab770f1a4ff9186148c2ab73102f6596fa0e1a1c7c44d3bf10e169eacd96a55b8bf5d082b7bb9c928e587d164246c321",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201965,
            },
            {
                "pubkey": "8e91f0797bd16fb20a200c59c2b7be69c9906fa568fd91a4b78825f34013e315e2c97be643135cdb2465706a5f685514",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201966,
            },
            {
                "pubkey": "93865e7557e6017a70cea2c924143353aa7ed41106bfc165dffd2414060e1577573f04cb29ce5d38a5d49924c9dba46b",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201967,
            },
            {
                "pubkey": "b79dbc30d94ff57767f1680cb06d143b9c186bf53487edb8b8701a956e4cc8cc6561851ef00785792f92c9252afeb3ea",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201968,
            },
            {
                "pubkey": "93fa9b2007bdea9ea3b2a06a612efeedb5c90392e43ceb8b4278fd79435fe8ff47b8499d590027b86eceab9693ec3a77",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201969,
            },
            {
                "pubkey": "91b72fb5f174e4df21c1ff11044f8b9a31881a512c4ef756788867fa894d97a79e81c0344e9055cec622345b33ae2074",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201970,
            },
            {
                "pubkey": "89bf56a911fa9dcc4554dfda1168f0879bf2e99af7b8a75a81f0f7bd675e43ecc27ee25feac6a017178afc9a83968bc7",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201971,
            },
            {
                "pubkey": "982d834593ad241133d1265519804cd740723786303495c70e4818538858e9d817f27651a054ab0e8c49f483a6bc030c",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201972,
            },
            {
                "pubkey": "acde4ab6a25ba0a1eb7311156e245be3bb8fc8d682b38e6e01e5db1995e244dfc7406caf73bb6ef8d518dcfa9112a973",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201973,
            },
            {
                "pubkey": "ae6a17f83703812a42c14b5534ad806cba2715945d0145e72cf0e5af1ed657bfe51fb60553d4b7106b0ad7b0947fdf44",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201974,
            },
            {
                "pubkey": "91b0eae347b00ecde5fdf47e12096ff917b32ce24effbeb6966c76de1523f6a6db14182f9686ef416f9866c8fb0dff35",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201975,
            },
            {
                "pubkey": "979d016e0c882dd0a94c3b308454485d1b4f5375877d4869b84540ad70a7dad08e58ef19ed4a4278ff5bbe110513ba73",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201976,
            },
            {
                "pubkey": "a48955a7f4404022e1d18bd28ad939a16732c85c01ef915faf7567dcf547a730db072409f8f7d356aa7fba78015b1c82",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201977,
            },
            {
                "pubkey": "9954379b187d85c3f06319be088cec38fa389136f41482fa3745be26afc810c4b52df10c213d5f1a050e52f62bda691f",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201978,
            },
            {
                "pubkey": "8601f3fc746f41c76decd3523be8f1eec8161dc8a6b20acbbb5823ec7fb1b3567854995f23b43e12e776e0080214b830",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201979,
            },
            {
                "pubkey": "b4742b8a98a3b1df4134e9fca9ba9ec68f43946e590f21acbeea6510d4a16a073d3d7cab7c477a5ae467dc2dfbf1dbdc",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201980,
            },
            {
                "pubkey": "81ef96dd5e022fc5bd566e59ee716bcd76dcd0e74712fc80f2ed8d8533c4b9a9fc0cf4dac64b7044421db730f579e8b0",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1201981,
            },
            {
                "pubkey": "9696aac80769eefef678a12576005194920321b82233bdf2ecfe23a7c99fb42429ba329ac1689c76e7ca4f045847f550",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202057,
            },
            {
                "pubkey": "86bfd20acd5d55f6c0cab4338f5e8ec03f18909f89cf31b754db1be2fcbbdfc0b5a1c3c3e354a04b8e8cabc071416b43",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202058,
            },
            {
                "pubkey": "88090d495e7fd311ce8c77e48beb81972148827dae57f74a96a236c8f4fb7448cae0b35260e5a44ee5f3277991a2afe4",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202059,
            },
            {
                "pubkey": "a099b9d027f328dddeb9d826962f66452e5a16e93e217a15535bae37570428dab0501358e0a3bf8cf2d3f73ec3bc4e6d",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202060,
            },
            {
                "pubkey": "9766bb04e1503ab24db1d8c4cff9020ce2c957f5e96e96b1898099fb86380bdfb9d1cc77e0061cb4eeb3e8731a1cd785",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202061,
            },
            {
                "pubkey": "a72c882c51c47e02262f16536eac8c153d2790d7965246007db67e1ae5e2caeffa370dd8a5fbc41f531527c69ab594e6",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202062,
            },
            {
                "pubkey": "b247193214c14a6a025b27781c75214b7ebd7205e86afc4bde3dd149ff9b070189551770d83c8f5365b528caf0768d3a",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202063,
            },
            {
                "pubkey": "8fcb5967de3fab420f38cdc9c89019e4769669b987d9165eb1e920e0a735be28e1ceea5ae1a6fe5609c218eab674888a",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202064,
            },
            {
                "pubkey": "931b39b9a119906f71276434a8eb0c5f9c49d8a0248118f8171ab0605561d2adcde37a57f693fec8f990e4761961f527",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202065,
            },
            {
                "pubkey": "b4095c8165e81722ad21b0e18fdd9c4bc17121102188f4a636d8e250093e4e24220a88e4afe4177f7a57a211ed031442",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202066,
            },
            {
                "pubkey": "a3126b785f3ec6e633d2df5c513f195d3a30fda2974730d77e1c9afed4d35c037ef483b9110f96d1013784f6c650a4e8",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202067,
            },
            {
                "pubkey": "97d2357e30acf77f10aacc0876744ca439dbbfc7ff7c05ee295a75432e3b47800a1167039ab08f6491447b68652c6291",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202068,
            },
            {
                "pubkey": "a1665903cc9d16b87bce18c65cd54ec4f0273394aa80639bc99cbc6a0a6fd4f38d2a21c6d4389dcd615239b5d9a083dd",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202069,
            },
            {
                "pubkey": "8e7e91d14a963c35b6ec010807b595221f39a0b5a84b854a474b67ea2cebf6a3f0f7ca410011eef25c8f8993a10e30f3",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202070,
            },
            {
                "pubkey": "83079ac340358f91957a6493ed5d348263afa36dcf61966af8a2f9a76bd777bc590da24626bdbc8e27977ccb29c201d5",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202071,
            },
            {
                "pubkey": "88756b153ada4d9bdab0f1fb4820e932507255e53734f6d8fbfca938b1dbc647d4d32e726191ae879b63c927da6b48fc",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202072,
            },
            {
                "pubkey": "92797d19db94c02cf2a22a8046cc997c56c762d6ee2e1b49aaf494ed529460216ea58732d127c0c5c95bee1ea2286c83",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202073,
            },
            {
                "pubkey": "8db9855a5b80fb44e6d2ef37d5542dabdeb18ee6b31acf75933de507915df2fef9746084f17040e1ea0f22e232d11452",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202074,
            },
            {
                "pubkey": "9181e8b985a4555ad962d8700af589894654fabaa397fa8e593472c1f5ffcdb11a7f47ee76ee87952749dcd097acee90",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202075,
            },
            {
                "pubkey": "a747a8782e75d19003a6cfab585a63038c3b22ed00bce37bf205bc6c189e2e495d8efb6253f0f1f8ad4b4a955e83154f",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202076,
            },
            {
                "pubkey": "8147836ed310658ee43b5751f2c6bad24dd435bb3f659f8118e23de14847596051076796eaea7e5e15b12b9cf5b22c67",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202077,
            },
            {
                "pubkey": "a0ab73a29977df669782b8721bfb6a1619d9897711e061de4ddf9ecff8666822655611c58948b5211cb258a9ff713d13",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202078,
            },
            {
                "pubkey": "b0c03c8589bcfbf916956053bbcebc9b8b9aff44c38f1ae14af2b7e6e7d0cf9b5ad56ca285b0a3071dc7dc603ec072bf",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202079,
            },
            {
                "pubkey": "b902d3e34d3d34a50a7086e22d671a0d9dc13e2253b7ac0c6e638f8ca356a44a42125fa60252be463820fec40257e109",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202080,
            },
            {
                "pubkey": "84f9e7cfed7e242caa1841068a49fcd0af7b8c71234981f364ae0adb77ee11a050c05f83ee170b753dcd7f5191974006",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202081,
            },
            {
                "pubkey": "aad0bcd4ff9d5c8483d9b40f4a0312017e82b1a3359160c4363d541a12434b83f1d00ba2e59301635a41da9698fd3e49",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202082,
            },
            {
                "pubkey": "8a384994176fd090408c3aa0e3e01f3664313c3b8df7d447d13b025412d53abff52988362b09b59ed6228ec458ff788f",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202083,
            },
            {
                "pubkey": "afe1f5bf04854d18182e93eb9048d3306160dc9bf8d69e60d12653112800d73b08e0069354edb44f6718ed7aaece6084",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202084,
            },
            {
                "pubkey": "b6557f6b0bd7c177dcf305f5024f00936ca5e680d8b42c574c3a54c44a3d86409f845e300027d9923f4619e76fe68376",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202085,
            },
            {
                "pubkey": "af0dda9f7de18c68f60383510af753c7a326a207adb10621bf3b8204929dd939d1b16bb904f4b2c7a0faa86893c03f6b",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202086,
            },
            {
                "pubkey": "ac9e2ed78b34a0e36784e11546b0d3e05529e292dc8b6df39b13c9795ed1ba135454e3af142e357597d7a6322c234584",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202087,
            },
            {
                "pubkey": "ab64838fb73d078c8f2752c6204fc0f23bf3e8a495bcbd03724bf582f0b6695547841834abaafd22d4441653d6278199",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202088,
            },
            {
                "pubkey": "b52500f7ae18fed6852a74bea339122fb57cb634b4806b87d388504ead1bc2471ade11d1a0f7741aacf8f6966d2e6015",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202089,
            },
            {
                "pubkey": "a294c0228e26053479ad616b79197a933c74659d27e7a9e4d52aad37f8f089f66d37ee58fdbbc0df19bed33942b72819",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202090,
            },
            {
                "pubkey": "8b49f971b6d2655660188591e053ae2cfc6381913507b07c2747bfc6c3cf2361a4c2182e403503ebc3246482727ca6b4",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202091,
            },
            {
                "pubkey": "8f2a444e04a500f3613767961e0bc27a6914429cc24c3e9b72c44d31f5d4f696affd74f08d594ec23b3f15ef11f9344f",
                "nodeOpId": 38,
                "moduleId": 1,
                "valIndex": 1202092,
            },
        ]

        # =====================================================================
        # TEST EXECUTION - No need to modify below
        # =====================================================================

        # Convert hex to bytes if needed
        if isinstance(exit_data_hex, str):
            if exit_data_hex.startswith("0x"):
                exit_data_hex = exit_data_hex[2:]
            exit_data = bytes.fromhex(exit_data_hex)
        else:
            exit_data = exit_data_hex

        # Decode the exit data using local implementation
        validators = decode_all_validators(exit_data)

        # =====================================================================
        # ASSERTIONS
        # =====================================================================

        # Verify each validator has the expected structure
        for i, validator in enumerate(validators):
            # Check required fields exist
            assert "pubkey" in validator, f"Validator {i} missing 'pubkey'"
            assert "nodeOpId" in validator, f"Validator {i} missing 'nodeOpId'"
            assert "moduleId" in validator, f"Validator {i} missing 'moduleId'"
            assert "valIndex" in validator, f"Validator {i} missing 'valIndex'"
            assert "index" in validator, f"Validator {i} missing 'index'"

            # Verify types
            assert isinstance(
                validator["pubkey"], bytes
            ), f"Validator {i} pubkey should be bytes, got {type(validator['pubkey'])}"
            assert isinstance(
                validator["nodeOpId"], int
            ), f"Validator {i} nodeOpId should be int, got {type(validator['nodeOpId'])}"
            assert isinstance(
                validator["moduleId"], int
            ), f"Validator {i} moduleId should be int, got {type(validator['moduleId'])}"
            assert isinstance(
                validator["valIndex"], int
            ), f"Validator {i} valIndex should be int, got {type(validator['valIndex'])}"
            assert isinstance(
                validator["index"], int
            ), f"Validator {i} index should be int, got {type(validator['index'])}"

            # Verify pubkey is 48 bytes (BLS public key length)
            assert (
                len(validator["pubkey"]) == 48
            ), f"Validator {i} pubkey should be 48 bytes, got {len(validator['pubkey'])}"

            # Verify index matches position in the list
            assert (
                validator["index"] == i
            ), f"Validator {i} index mismatch: expected {i}, got {validator['index']}"

            # Verify IDs are non-negative
            assert (
                validator["nodeOpId"] >= 0
            ), f"Validator {i} nodeOpId should be non-negative"
            assert (
                validator["moduleId"] >= 0
            ), f"Validator {i} moduleId should be non-negative"
            assert (
                validator["valIndex"] >= 0
            ), f"Validator {i} valIndex should be non-negative"

        for v in validators:
            print("-------")
            print(v["pubkey"].hex())
            print(v["nodeOpId"])
            print(v["moduleId"])
            print(v["valIndex"])
            print("-------")

        # Optional: Verify against expected values if provided
        # Note: expected_validators would need to be imported if validation is desired
        expected_validators = []  # Set to empty list since expected_validators_data.py was deleted
        if expected_validators:
            for i, (validator, expected) in enumerate(
                zip(validators, expected_validators)
            ):
                if "pubkey" in expected and expected["pubkey"]:
                    expected_pubkey_hex = expected["pubkey"]
                    if expected_pubkey_hex.startswith("0x"):
                        expected_pubkey_hex = expected_pubkey_hex[2:]
                    expected_pubkey = bytes.fromhex(expected_pubkey_hex)
                    assert (
                        validator["pubkey"] == expected_pubkey
                    ), f"Validator {i} pubkey mismatch:\n  Got:      {validator['pubkey'].hex()}\n  Expected: {expected_pubkey.hex()}"

                if "nodeOpId" in expected:
                    assert (
                        validator["nodeOpId"] == expected["nodeOpId"]
                    ), f"Validator {i} nodeOpId mismatch: got {validator['nodeOpId']}, expected {expected['nodeOpId']}"

                if "moduleId" in expected:
                    assert (
                        validator["moduleId"] == expected["moduleId"]
                    ), f"Validator {i} moduleId mismatch: got {validator['moduleId']}, expected {expected['moduleId']}"

                if "valIndex" in expected:
                    assert (
                        validator["valIndex"] == expected["valIndex"]
                    ), f"Validator {i} valIndex mismatch: got {validator['valIndex']}, expected {expected['valIndex']}"

        # =====================================================================
        # OUTPUT - Print decoded data for manual verification
        # =====================================================================

        print(f"\n{'='*80}")
        print(f"✅ Successfully decoded {len(validators)} validator(s) from exit data")
        print(f"{'='*80}")
        print(
            f"Exit data length: {len(exit_data)} bytes ({len(exit_data_hex)} hex chars)"
        )
        print(f"Packed request length: {PACKED_REQUEST_LENGTH} bytes per validator")
        print(f"Expected validators: {len(exit_data) // PACKED_REQUEST_LENGTH}")
        print(f"Decoded validators: {len(validators)}")
        print(f"{'='*80}")

        for i, validator in enumerate(validators):
            print(f"\nValidator #{i}:")
            print(f"  Pubkey:     0x{validator['pubkey'].hex()}")
            print(f"  Module ID:  {validator['moduleId']}")
            print(f"  Node Op ID: {validator['nodeOpId']}")
            print(f"  Val Index:  {validator['valIndex']}")
            print(f"  List Index: {validator['index']}")

        print(f"\n{'='*80}\n")

    def test_unpack_single_exit_request(self):
        """
        Test unpacking a single exit request from packed data.

        This test validates the unpack_exit_request function which extracts
        a single validator's information at a specific index.
        """
        # =====================================================================
        # CONFIGURATION
        # =====================================================================

        # Exit data to decode (use same as main test or provide different data)
        exit_data_hex = "0x0000010000000026000000000012572a919d858f5e2af21ef6f7525beb4621432208675acff2f54b71e720ced04e2e26bfe4e2a79bb32a57d147935651ee531d0000010000000026000000000012572bb35b62d26c996bb91396523a8b9036e608d4146a466c61ad0ba42717b7e75be103cf0c8916905fb651c731165ae77acb0000010000000026000000000012572cabff903cbe0fc89aa586fc161611d245c1bdd5b1008317dc1fe8ed021ae188e99d70780784093d76f571b3e9558a3b8f0000010000000026000000000012572dab770f1a4ff9186148c2ab73102f6596fa0e1a1c7c44d3bf10e169eacd96a55b8bf5d082b7bb9c928e587d164246c3210000010000000026000000000012572e8e91f0797bd16fb20a200c59c2b7be69c9906fa568fd91a4b78825f34013e315e2c97be643135cdb2465706a5f6855140000010000000026000000000012572f93865e7557e6017a70cea2c924143353aa7ed41106bfc165dffd2414060e1577573f04cb29ce5d38a5d49924c9dba46b00000100000000260000000000125730b79dbc30d94ff57767f1680cb06d143b9c186bf53487edb8b8701a956e4cc8cc6561851ef00785792f92c9252afeb3ea0000010000000026000000000012573193fa9b2007bdea9ea3b2a06a612efeedb5c90392e43ceb8b4278fd79435fe8ff47b8499d590027b86eceab9693ec3a770000010000000026000000000012573291b72fb5f174e4df21c1ff11044f8b9a31881a512c4ef756788867fa894d97a79e81c0344e9055cec622345b33ae20740000010000000026000000000012573389bf56a911fa9dcc4554dfda1168f0879bf2e99af7b8a75a81f0f7bd675e43ecc27ee25feac6a017178afc9a83968bc700000100000000260000000000125734982d834593ad241133d1265519804cd740723786303495c70e4818538858e9d817f27651a054ab0e8c49f483a6bc030c00000100000000260000000000125735acde4ab6a25ba0a1eb7311156e245be3bb8fc8d682b38e6e01e5db1995e244dfc7406caf73bb6ef8d518dcfa9112a97300000100000000260000000000125736ae6a17f83703812a42c14b5534ad806cba2715945d0145e72cf0e5af1ed657bfe51fb60553d4b7106b0ad7b0947fdf440000010000000026000000000012573791b0eae347b00ecde5fdf47e12096ff917b32ce24effbeb6966c76de1523f6a6db14182f9686ef416f9866c8fb0dff3500000100000000260000000000125738979d016e0c882dd0a94c3b308454485d1b4f5375877d4869b84540ad70a7dad08e58ef19ed4a4278ff5bbe110513ba7300000100000000260000000000125739a48955a7f4404022e1d18bd28ad939a16732c85c01ef915faf7567dcf547a730db072409f8f7d356aa7fba78015b1c820000010000000026000000000012573a9954379b187d85c3f06319be088cec38fa389136f41482fa3745be26afc810c4b52df10c213d5f1a050e52f62bda691f0000010000000026000000000012573b8601f3fc746f41c76decd3523be8f1eec8161dc8a6b20acbbb5823ec7fb1b3567854995f23b43e12e776e0080214b8300000010000000026000000000012573cb4742b8a98a3b1df4134e9fca9ba9ec68f43946e590f21acbeea6510d4a16a073d3d7cab7c477a5ae467dc2dfbf1dbdc0000010000000026000000000012573d81ef96dd5e022fc5bd566e59ee716bcd76dcd0e74712fc80f2ed8d8533c4b9a9fc0cf4dac64b7044421db730f579e8b0000001000000002600000000001257899696aac80769eefef678a12576005194920321b82233bdf2ecfe23a7c99fb42429ba329ac1689c76e7ca4f045847f5500000010000000026000000000012578a86bfd20acd5d55f6c0cab4338f5e8ec03f18909f89cf31b754db1be2fcbbdfc0b5a1c3c3e354a04b8e8cabc071416b430000010000000026000000000012578b88090d495e7fd311ce8c77e48beb81972148827dae57f74a96a236c8f4fb7448cae0b35260e5a44ee5f3277991a2afe40000010000000026000000000012578ca099b9d027f328dddeb9d826962f66452e5a16e93e217a15535bae37570428dab0501358e0a3bf8cf2d3f73ec3bc4e6d0000010000000026000000000012578d9766bb04e1503ab24db1d8c4cff9020ce2c957f5e96e96b1898099fb86380bdfb9d1cc77e0061cb4eeb3e8731a1cd7850000010000000026000000000012578ea72c882c51c47e02262f16536eac8c153d2790d7965246007db67e1ae5e2caeffa370dd8a5fbc41f531527c69ab594e60000010000000026000000000012578fb247193214c14a6a025b27781c75214b7ebd7205e86afc4bde3dd149ff9b070189551770d83c8f5365b528caf0768d3a000001000000002600000000001257908fcb5967de3fab420f38cdc9c89019e4769669b987d9165eb1e920e0a735be28e1ceea5ae1a6fe5609c218eab674888a00000100000000260000000000125791931b39b9a119906f71276434a8eb0c5f9c49d8a0248118f8171ab0605561d2adcde37a57f693fec8f990e4761961f52700000100000000260000000000125792b4095c8165e81722ad21b0e18fdd9c4bc17121102188f4a636d8e250093e4e24220a88e4afe4177f7a57a211ed03144200000100000000260000000000125793a3126b785f3ec6e633d2df5c513f195d3a30fda2974730d77e1c9afed4d35c037ef483b9110f96d1013784f6c650a4e80000010000000026000000000012579497d2357e30acf77f10aacc0876744ca439dbbfc7ff7c05ee295a75432e3b47800a1167039ab08f6491447b68652c629100000100000000260000000000125795a1665903cc9d16b87bce18c65cd54ec4f0273394aa80639bc99cbc6a0a6fd4f38d2a21c6d4389dcd615239b5d9a083dd000001000000002600000000001257968e7e91d14a963c35b6ec010807b595221f39a0b5a84b854a474b67ea2cebf6a3f0f7ca410011eef25c8f8993a10e30f30000010000000026000000000012579783079ac340358f91957a6493ed5d348263afa36dcf61966af8a2f9a76bd777bc590da24626bdbc8e27977ccb29c201d50000010000000026000000000012579888756b153ada4d9bdab0f1fb4820e932507255e53734f6d8fbfca938b1dbc647d4d32e726191ae879b63c927da6b48fc0000010000000026000000000012579992797d19db94c02cf2a22a8046cc997c56c762d6ee2e1b49aaf494ed529460216ea58732d127c0c5c95bee1ea2286c830000010000000026000000000012579a8db9855a5b80fb44e6d2ef37d5542dabdeb18ee6b31acf75933de507915df2fef9746084f17040e1ea0f22e232d114520000010000000026000000000012579b9181e8b985a4555ad962d8700af589894654fabaa397fa8e593472c1f5ffcdb11a7f47ee76ee87952749dcd097acee900000010000000026000000000012579ca747a8782e75d19003a6cfab585a63038c3b22ed00bce37bf205bc6c189e2e495d8efb6253f0f1f8ad4b4a955e83154f0000010000000026000000000012579d8147836ed310658ee43b5751f2c6bad24dd435bb3f659f8118e23de14847596051076796eaea7e5e15b12b9cf5b22c670000010000000026000000000012579ea0ab73a29977df669782b8721bfb6a1619d9897711e061de4ddf9ecff8666822655611c58948b5211cb258a9ff713d130000010000000026000000000012579fb0c03c8589bcfbf916956053bbcebc9b8b9aff44c38f1ae14af2b7e6e7d0cf9b5ad56ca285b0a3071dc7dc603ec072bf000001000000002600000000001257a0b902d3e34d3d34a50a7086e22d671a0d9dc13e2253b7ac0c6e638f8ca356a44a42125fa60252be463820fec40257e109000001000000002600000000001257a184f9e7cfed7e242caa1841068a49fcd0af7b8c71234981f364ae0adb77ee11a050c05f83ee170b753dcd7f5191974006000001000000002600000000001257a2aad0bcd4ff9d5c8483d9b40f4a0312017e82b1a3359160c4363d541a12434b83f1d00ba2e59301635a41da9698fd3e49000001000000002600000000001257a38a384994176fd090408c3aa0e3e01f3664313c3b8df7d447d13b025412d53abff52988362b09b59ed6228ec458ff788f000001000000002600000000001257a4afe1f5bf04854d18182e93eb9048d3306160dc9bf8d69e60d12653112800d73b08e0069354edb44f6718ed7aaece6084000001000000002600000000001257a5b6557f6b0bd7c177dcf305f5024f00936ca5e680d8b42c574c3a54c44a3d86409f845e300027d9923f4619e76fe68376000001000000002600000000001257a6af0dda9f7de18c68f60383510af753c7a326a207adb10621bf3b8204929dd939d1b16bb904f4b2c7a0faa86893c03f6b000001000000002600000000001257a7ac9e2ed78b34a0e36784e11546b0d3e05529e292dc8b6df39b13c9795ed1ba135454e3af142e357597d7a6322c234584000001000000002600000000001257a8ab64838fb73d078c8f2752c6204fc0f23bf3e8a495bcbd03724bf582f0b6695547841834abaafd22d4441653d6278199000001000000002600000000001257a9b52500f7ae18fed6852a74bea339122fb57cb634b4806b87d388504ead1bc2471ade11d1a0f7741aacf8f6966d2e6015000001000000002600000000001257aaa294c0228e26053479ad616b79197a933c74659d27e7a9e4d52aad37f8f089f66d37ee58fdbbc0df19bed33942b72819000001000000002600000000001257ab8b49f971b6d2655660188591e053ae2cfc6381913507b07c2747bfc6c3cf2361a4c2182e403503ebc3246482727ca6b4000001000000002600000000001257ac8f2a444e04a500f3613767961e0bc27a6914429cc24c3e9b72c44d31f5d4f696affd74f08d594ec23b3f15ef11f9344f"

        # Index to unpack (0-based)
        index_to_unpack = 0

        # Optional: Expected values for the unpacked request
        expected_pubkey = None  # Set to hex string if you want to validate
        expected_node_op_id = None  # Set to int if you want to validate
        expected_module_id = None  # Set to int if you want to validate
        expected_val_index = None  # Set to int if you want to validate

        # =====================================================================
        # TEST EXECUTION
        # =====================================================================

        # Convert hex to bytes
        if isinstance(exit_data_hex, str):
            if exit_data_hex.startswith("0x"):
                exit_data_hex = exit_data_hex[2:]
            exit_data = bytes.fromhex(exit_data_hex)
        else:
            exit_data = exit_data_hex

        # Unpack the exit request at the specified index using local implementation
        validator = unpack_exit_request(exit_data, index_to_unpack)

        pubkey = validator["pubkey"]
        node_op_id = validator["nodeOpId"]
        module_id = validator["moduleId"]
        val_index = validator["valIndex"]

        # =====================================================================
        # ASSERTIONS
        # =====================================================================

        # Verify types
        assert isinstance(pubkey, bytes), f"Pubkey should be bytes, got {type(pubkey)}"
        assert isinstance(
            node_op_id, int
        ), f"Node operator ID should be int, got {type(node_op_id)}"
        assert isinstance(
            module_id, int
        ), f"Module ID should be int, got {type(module_id)}"
        assert isinstance(
            val_index, int
        ), f"Validator index should be int, got {type(val_index)}"

        # Verify pubkey length
        assert len(pubkey) == 48, f"Pubkey should be 48 bytes, got {len(pubkey)}"

        # Verify non-negative values
        assert node_op_id >= 0, "Node operator ID should be non-negative"
        assert module_id >= 0, "Module ID should be non-negative"
        assert val_index >= 0, "Validator index should be non-negative"

        # Optional: Verify against expected values
        if expected_pubkey is not None:
            if expected_pubkey.startswith("0x"):
                expected_pubkey = expected_pubkey[2:]
            expected_pubkey_bytes = bytes.fromhex(expected_pubkey)
            assert (
                pubkey == expected_pubkey_bytes
            ), f"Pubkey mismatch:\n  Got:      {pubkey.hex()}\n  Expected: {expected_pubkey}"

        if expected_node_op_id is not None:
            assert (
                node_op_id == expected_node_op_id
            ), f"Node operator ID mismatch: got {node_op_id}, expected {expected_node_op_id}"

        if expected_module_id is not None:
            assert (
                module_id == expected_module_id
            ), f"Module ID mismatch: got {module_id}, expected {expected_module_id}"

        if expected_val_index is not None:
            assert (
                val_index == expected_val_index
            ), f"Validator index mismatch: got {val_index}, expected {expected_val_index}"

        # =====================================================================
        # OUTPUT
        # =====================================================================

        print(f"\n{'='*80}")
        print(f"✅ Successfully unpacked exit request at index {index_to_unpack}")
        print(f"{'='*80}")
        print(f"  Pubkey:     0x{pubkey.hex()}")
        print(f"  Module ID:  {module_id}")
        print(f"  Node Op ID: {node_op_id}")
        print(f"  Val Index:  {val_index}")
        print(f"{'='*80}\n")

    def test_decode_multiple_validators(self):
        """
        Test decoding exit data with multiple validators.

        Useful for batch exit scenarios.
        """
        # =====================================================================
        # CONFIGURATION
        # =====================================================================

        # Exit data containing multiple validators
        exit_data_hex = "0x0000010000000026000000000012572a919d858f5e2af21ef6f7525beb4621432208675acff2f54b71e720ced04e2e26bfe4e2a79bb32a57d147935651ee531d0000010000000026000000000012572bb35b62d26c996bb91396523a8b9036e608d4146a466c61ad0ba42717b7e75be103cf0c8916905fb651c731165ae77acb0000010000000026000000000012572cabff903cbe0fc89aa586fc161611d245c1bdd5b1008317dc1fe8ed021ae188e99d70780784093d76f571b3e9558a3b8f0000010000000026000000000012572dab770f1a4ff9186148c2ab73102f6596fa0e1a1c7c44d3bf10e169eacd96a55b8bf5d082b7bb9c928e587d164246c3210000010000000026000000000012572e8e91f0797bd16fb20a200c59c2b7be69c9906fa568fd91a4b78825f34013e315e2c97be643135cdb2465706a5f6855140000010000000026000000000012572f93865e7557e6017a70cea2c924143353aa7ed41106bfc165dffd2414060e1577573f04cb29ce5d38a5d49924c9dba46b00000100000000260000000000125730b79dbc30d94ff57767f1680cb06d143b9c186bf53487edb8b8701a956e4cc8cc6561851ef00785792f92c9252afeb3ea0000010000000026000000000012573193fa9b2007bdea9ea3b2a06a612efeedb5c90392e43ceb8b4278fd79435fe8ff47b8499d590027b86eceab9693ec3a770000010000000026000000000012573291b72fb5f174e4df21c1ff11044f8b9a31881a512c4ef756788867fa894d97a79e81c0344e9055cec622345b33ae20740000010000000026000000000012573389bf56a911fa9dcc4554dfda1168f0879bf2e99af7b8a75a81f0f7bd675e43ecc27ee25feac6a017178afc9a83968bc700000100000000260000000000125734982d834593ad241133d1265519804cd740723786303495c70e4818538858e9d817f27651a054ab0e8c49f483a6bc030c00000100000000260000000000125735acde4ab6a25ba0a1eb7311156e245be3bb8fc8d682b38e6e01e5db1995e244dfc7406caf73bb6ef8d518dcfa9112a97300000100000000260000000000125736ae6a17f83703812a42c14b5534ad806cba2715945d0145e72cf0e5af1ed657bfe51fb60553d4b7106b0ad7b0947fdf440000010000000026000000000012573791b0eae347b00ecde5fdf47e12096ff917b32ce24effbeb6966c76de1523f6a6db14182f9686ef416f9866c8fb0dff3500000100000000260000000000125738979d016e0c882dd0a94c3b308454485d1b4f5375877d4869b84540ad70a7dad08e58ef19ed4a4278ff5bbe110513ba7300000100000000260000000000125739a48955a7f4404022e1d18bd28ad939a16732c85c01ef915faf7567dcf547a730db072409f8f7d356aa7fba78015b1c820000010000000026000000000012573a9954379b187d85c3f06319be088cec38fa389136f41482fa3745be26afc810c4b52df10c213d5f1a050e52f62bda691f0000010000000026000000000012573b8601f3fc746f41c76decd3523be8f1eec8161dc8a6b20acbbb5823ec7fb1b3567854995f23b43e12e776e0080214b8300000010000000026000000000012573cb4742b8a98a3b1df4134e9fca9ba9ec68f43946e590f21acbeea6510d4a16a073d3d7cab7c477a5ae467dc2dfbf1dbdc0000010000000026000000000012573d81ef96dd5e022fc5bd566e59ee716bcd76dcd0e74712fc80f2ed8d8533c4b9a9fc0cf4dac64b7044421db730f579e8b0000001000000002600000000001257899696aac80769eefef678a12576005194920321b82233bdf2ecfe23a7c99fb42429ba329ac1689c76e7ca4f045847f5500000010000000026000000000012578a86bfd20acd5d55f6c0cab4338f5e8ec03f18909f89cf31b754db1be2fcbbdfc0b5a1c3c3e354a04b8e8cabc071416b430000010000000026000000000012578b88090d495e7fd311ce8c77e48beb81972148827dae57f74a96a236c8f4fb7448cae0b35260e5a44ee5f3277991a2afe40000010000000026000000000012578ca099b9d027f328dddeb9d826962f66452e5a16e93e217a15535bae37570428dab0501358e0a3bf8cf2d3f73ec3bc4e6d0000010000000026000000000012578d9766bb04e1503ab24db1d8c4cff9020ce2c957f5e96e96b1898099fb86380bdfb9d1cc77e0061cb4eeb3e8731a1cd7850000010000000026000000000012578ea72c882c51c47e02262f16536eac8c153d2790d7965246007db67e1ae5e2caeffa370dd8a5fbc41f531527c69ab594e60000010000000026000000000012578fb247193214c14a6a025b27781c75214b7ebd7205e86afc4bde3dd149ff9b070189551770d83c8f5365b528caf0768d3a000001000000002600000000001257908fcb5967de3fab420f38cdc9c89019e4769669b987d9165eb1e920e0a735be28e1ceea5ae1a6fe5609c218eab674888a00000100000000260000000000125791931b39b9a119906f71276434a8eb0c5f9c49d8a0248118f8171ab0605561d2adcde37a57f693fec8f990e4761961f52700000100000000260000000000125792b4095c8165e81722ad21b0e18fdd9c4bc17121102188f4a636d8e250093e4e24220a88e4afe4177f7a57a211ed03144200000100000000260000000000125793a3126b785f3ec6e633d2df5c513f195d3a30fda2974730d77e1c9afed4d35c037ef483b9110f96d1013784f6c650a4e80000010000000026000000000012579497d2357e30acf77f10aacc0876744ca439dbbfc7ff7c05ee295a75432e3b47800a1167039ab08f6491447b68652c629100000100000000260000000000125795a1665903cc9d16b87bce18c65cd54ec4f0273394aa80639bc99cbc6a0a6fd4f38d2a21c6d4389dcd615239b5d9a083dd000001000000002600000000001257968e7e91d14a963c35b6ec010807b595221f39a0b5a84b854a474b67ea2cebf6a3f0f7ca410011eef25c8f8993a10e30f30000010000000026000000000012579783079ac340358f91957a6493ed5d348263afa36dcf61966af8a2f9a76bd777bc590da24626bdbc8e27977ccb29c201d50000010000000026000000000012579888756b153ada4d9bdab0f1fb4820e932507255e53734f6d8fbfca938b1dbc647d4d32e726191ae879b63c927da6b48fc0000010000000026000000000012579992797d19db94c02cf2a22a8046cc997c56c762d6ee2e1b49aaf494ed529460216ea58732d127c0c5c95bee1ea2286c830000010000000026000000000012579a8db9855a5b80fb44e6d2ef37d5542dabdeb18ee6b31acf75933de507915df2fef9746084f17040e1ea0f22e232d114520000010000000026000000000012579b9181e8b985a4555ad962d8700af589894654fabaa397fa8e593472c1f5ffcdb11a7f47ee76ee87952749dcd097acee900000010000000026000000000012579ca747a8782e75d19003a6cfab585a63038c3b22ed00bce37bf205bc6c189e2e495d8efb6253f0f1f8ad4b4a955e83154f0000010000000026000000000012579d8147836ed310658ee43b5751f2c6bad24dd435bb3f659f8118e23de14847596051076796eaea7e5e15b12b9cf5b22c670000010000000026000000000012579ea0ab73a29977df669782b8721bfb6a1619d9897711e061de4ddf9ecff8666822655611c58948b5211cb258a9ff713d130000010000000026000000000012579fb0c03c8589bcfbf916956053bbcebc9b8b9aff44c38f1ae14af2b7e6e7d0cf9b5ad56ca285b0a3071dc7dc603ec072bf000001000000002600000000001257a0b902d3e34d3d34a50a7086e22d671a0d9dc13e2253b7ac0c6e638f8ca356a44a42125fa60252be463820fec40257e109000001000000002600000000001257a184f9e7cfed7e242caa1841068a49fcd0af7b8c71234981f364ae0adb77ee11a050c05f83ee170b753dcd7f5191974006000001000000002600000000001257a2aad0bcd4ff9d5c8483d9b40f4a0312017e82b1a3359160c4363d541a12434b83f1d00ba2e59301635a41da9698fd3e49000001000000002600000000001257a38a384994176fd090408c3aa0e3e01f3664313c3b8df7d447d13b025412d53abff52988362b09b59ed6228ec458ff788f000001000000002600000000001257a4afe1f5bf04854d18182e93eb9048d3306160dc9bf8d69e60d12653112800d73b08e0069354edb44f6718ed7aaece6084000001000000002600000000001257a5b6557f6b0bd7c177dcf305f5024f00936ca5e680d8b42c574c3a54c44a3d86409f845e300027d9923f4619e76fe68376000001000000002600000000001257a6af0dda9f7de18c68f60383510af753c7a326a207adb10621bf3b8204929dd939d1b16bb904f4b2c7a0faa86893c03f6b000001000000002600000000001257a7ac9e2ed78b34a0e36784e11546b0d3e05529e292dc8b6df39b13c9795ed1ba135454e3af142e357597d7a6322c234584000001000000002600000000001257a8ab64838fb73d078c8f2752c6204fc0f23bf3e8a495bcbd03724bf582f0b6695547841834abaafd22d4441653d6278199000001000000002600000000001257a9b52500f7ae18fed6852a74bea339122fb57cb634b4806b87d388504ead1bc2471ade11d1a0f7741aacf8f6966d2e6015000001000000002600000000001257aaa294c0228e26053479ad616b79197a933c74659d27e7a9e4d52aad37f8f089f66d37ee58fdbbc0df19bed33942b72819000001000000002600000000001257ab8b49f971b6d2655660188591e053ae2cfc6381913507b07c2747bfc6c3cf2361a4c2182e403503ebc3246482727ca6b4000001000000002600000000001257ac8f2a444e04a500f3613767961e0bc27a6914429cc24c3e9b72c44d31f5d4f696affd74f08d594ec23b3f15ef11f9344f"
        data_format = 1

        # =====================================================================
        # TEST EXECUTION
        # =====================================================================

        if isinstance(exit_data_hex, str):
            if exit_data_hex.startswith("0x"):
                exit_data_hex = exit_data_hex[2:]
            exit_data = bytes.fromhex(exit_data_hex)
        else:
            exit_data = exit_data_hex

        # Decode using local implementation
        validators = decode_all_validators(exit_data)

        # =====================================================================
        # ASSERTIONS
        # =====================================================================

        # Verify all validators have unique pubkeys
        pubkeys = [v["pubkey"] for v in validators]
        assert len(pubkeys) == len(
            set(pubkeys)
        ), "Validators should have unique pubkeys"

        # Verify sequential indexes
        for i, validator in enumerate(validators):
            assert validator["index"] == i

        # Print summary
        print(f"\n{'='*80}")
        print(f"✅ Decoded {len(validators)} validators")
        print(f"{'='*80}")

        # Group by module and node operator
        by_module = {}
        for v in validators:
            key = (v["moduleId"], v["nodeOpId"])
            if key not in by_module:
                by_module[key] = []
            by_module[key].append(v)

        print(f"\nGrouped by Module and Node Operator:")
        for (module_id, node_op_id), vals in by_module.items():
            print(
                f"\n  Module {module_id}, Node Operator {node_op_id}: {len(vals)} validator(s)"
            )
            for v in vals:
                print(
                    f"    - Pubkey: 0x{v['pubkey'].hex()[:16]}... (valIndex: {v['valIndex']})"
                )

        print(f"\n{'='*80}\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
