! rule: S7.2-004
! covers: intrinsic-assignment-pdt
! evidence: effect
program type_parameters_deferred_assignment_pdt
    implicit none
    integer, parameter :: family = kind(0)
    type :: packet(k, n)
        integer, kind :: k
        integer, len :: n
        integer :: payload(n)
    end type packet
    type(packet(family, 2)) :: short
    type(packet(family, 5)) :: long
    type(packet(family, :)), allocatable :: value

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

    value = short
    if (.not. allocated(value)) error stop 9
    if (value%k /= family) error stop 10
    if (kind(value%n) /= kind(0)) error stop 11
    if (value%n /= 2) error stop 12
    if (size(value%payload) /= 2) error stop 13
    if (lbound(value%payload, 1) /= 1) error stop 14
    if (any(value%payload /= [7, 11])) error stop 15

    value = long
    if (.not. allocated(value)) error stop 16
    if (value%k /= family) error stop 17
    if (kind(value%n) /= kind(0)) error stop 18
    if (value%n /= 5) error stop 19
    if (size(value%payload) /= 5) error stop 20
    if (lbound(value%payload, 1) /= 1) error stop 21
    if (any(value%payload /= [17, 19, 23, 29, 31])) error stop 22
end program type_parameters_deferred_assignment_pdt
