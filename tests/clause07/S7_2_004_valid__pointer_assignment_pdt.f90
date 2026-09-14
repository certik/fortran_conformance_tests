! rule: S7.2-004
! covers: pointer-assignment-pdt
! evidence: effect
program type_parameters_deferred_pointer_pdt
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
    if (kind(value%n) /= kind(0)) error stop 11
    if (value%n /= 2) error stop 12
    if (size(value%payload) /= 2) error stop 13
    if (lbound(value%payload, 1) /= 1) error stop 14
    if (.not. associated(value, first)) error stop 15
    if (any(value%payload /= [7, 11])) error stop 16

    value => second
    if (.not. associated(value)) error stop 17
    if (value%k /= family) error stop 18
    if (kind(value%n) /= kind(0)) error stop 19
    if (value%n /= 5) error stop 20
    if (size(value%payload) /= 5) error stop 21
    if (lbound(value%payload, 1) /= 1) error stop 22
    if (.not. associated(value, second)) error stop 23
    if (any(value%payload /= [17, 19, 23, 29, 31])) error stop 24
end program type_parameters_deferred_pointer_pdt
