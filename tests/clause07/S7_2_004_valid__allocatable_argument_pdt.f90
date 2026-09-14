! rule: S7.2-004
! covers: argument-association-pdt
! evidence: effect
program type_parameters_allocatable_argument_pdt
    implicit none
    integer, parameter :: family = kind(0)
    type :: packet(k, n)
        integer, kind :: k
        integer, len :: n
        integer :: payload(n)
    end type packet
    type(packet(family, :)), allocatable :: first, second
    integer :: status

    allocate(packet(family, 2) :: first, stat=status)
    if (status /= 0) error stop 1
    if (.not. allocated(first)) error stop 2
    if (first%k /= family) error stop 3
    if (first%n /= 2) error stop 4
    if (size(first%payload) /= 2) error stop 5
    if (lbound(first%payload, 1) /= 1) error stop 6
    first%payload(:) = [7, 11]
    call check_argument(first, 2, [7, 11])

    allocate(packet(family, 5) :: second, stat=status)
    if (status /= 0) error stop 7
    if (.not. allocated(second)) error stop 8
    if (second%k /= family) error stop 9
    if (second%n /= 5) error stop 10
    if (size(second%payload) /= 5) error stop 11
    if (lbound(second%payload, 1) /= 1) error stop 12
    second%payload(:) = [17, 19, 23, 29, 31]
    call check_argument(second, 5, [17, 19, 23, 29, 31])
contains
    subroutine check_argument(argument, expected_n, expected_payload)
        type(packet(family, :)), allocatable, intent(in) :: argument
        integer, intent(in) :: expected_n
        integer, intent(in) :: expected_payload(:)

        if (.not. allocated(argument)) error stop 13
        if (argument%k /= family) error stop 14
        if (kind(argument%n) /= kind(0)) error stop 15
        if (argument%n /= expected_n) error stop 16
        if (size(argument%payload) /= expected_n) error stop 17
        if (lbound(argument%payload, 1) /= 1) error stop 18
        if (size(expected_payload) /= expected_n) error stop 19
        if (any(argument%payload /= expected_payload)) error stop 20
    end subroutine check_argument
end program type_parameters_allocatable_argument_pdt
