! rule: S7.2-005
! covers: dummy-pdt
! evidence: effect
program type_parameters_assumed_dummy_pdt
    implicit none
    integer, parameter :: family = kind(0)
    type :: packet(k, n)
        integer, kind :: k
        integer, len :: n
        integer :: payload(n)
    end type packet
    type(packet(family, 2)) :: short
    type(packet(family, 5)) :: long

    if (short%k /= family) error stop 1
    if (short%n /= 2) error stop 2
    if (size(short%payload) /= 2) error stop 3
    if (lbound(short%payload, 1) /= 1) error stop 4
    short%payload(:) = [7, 11]
    if (long%k /= family) error stop 5
    if (long%n /= 5) error stop 6
    if (size(long%payload) /= 5) error stop 7
    if (lbound(long%payload, 1) /= 1) error stop 8
    long%payload(:) = [17, 19, 23, 29, 31]
    call check_argument(short, 2, [7, 11])
    call check_argument(long, 5, [17, 19, 23, 29, 31])
contains
    subroutine check_argument(argument, expected_n, expected_payload)
        type(packet(family, *)), intent(in) :: argument
        integer, intent(in) :: expected_n
        integer, intent(in) :: expected_payload(:)

        if (argument%k /= family) error stop 9
        if (kind(argument%n) /= kind(0)) error stop 10
        if (argument%n /= expected_n) error stop 11
        if (size(argument%payload) /= expected_n) error stop 12
        if (lbound(argument%payload, 1) /= 1) error stop 13
        if (size(expected_payload) /= expected_n) error stop 14
        if (any(argument%payload /= expected_payload)) error stop 15
    end subroutine check_argument
end program type_parameters_assumed_dummy_pdt
