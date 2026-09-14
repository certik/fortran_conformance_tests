! rule: S7.2-004
! covers: argument-association-pdt
! evidence: effect
program type_parameters_pointer_argument_pdt
    implicit none
    integer, parameter :: family = kind(0)
    type :: packet(k, n)
        integer, kind :: k
        integer, len :: n
        integer :: payload(n)
    end type packet
    type(packet(family, 2)), target :: first
    type(packet(family, 5)), target :: second
    type(packet(family, :)), pointer :: value => null()

    if (first%k /= family) error stop 1
    if (first%n /= 2) error stop 2
    if (size(first%payload) /= 2) error stop 3
    if (lbound(first%payload, 1) /= 1) error stop 4
    first%payload(:) = [7, 11]
    if (second%k /= family) error stop 5
    if (second%n /= 5) error stop 6
    if (size(second%payload) /= 5) error stop 7
    if (lbound(second%payload, 1) /= 1) error stop 8
    second%payload(:) = [17, 19, 23, 29, 31]

    value => first
    if (.not. associated(value)) error stop 9
    if (value%k /= family) error stop 10
    if (value%n /= 2) error stop 11
    if (size(value%payload) /= 2) error stop 12
    if (lbound(value%payload, 1) /= 1) error stop 13
    call check_argument(value, 2, [7, 11])

    value => second
    if (.not. associated(value)) error stop 14
    if (value%k /= family) error stop 15
    if (value%n /= 5) error stop 16
    if (size(value%payload) /= 5) error stop 17
    if (lbound(value%payload, 1) /= 1) error stop 18
    call check_argument(value, 5, [17, 19, 23, 29, 31])
contains
    subroutine check_argument(argument, expected_n, expected_payload)
        type(packet(family, :)), pointer, intent(in) :: argument
        integer, intent(in) :: expected_n
        integer, intent(in) :: expected_payload(:)

        if (.not. associated(argument)) error stop 19
        if (argument%k /= family) error stop 20
        if (kind(argument%n) /= kind(0)) error stop 21
        if (argument%n /= expected_n) error stop 22
        if (size(argument%payload) /= expected_n) error stop 23
        if (lbound(argument%payload, 1) /= 1) error stop 24
        if (size(expected_payload) /= expected_n) error stop 25
        if (any(argument%payload /= expected_payload)) error stop 26
    end subroutine check_argument
end program type_parameters_pointer_argument_pdt
