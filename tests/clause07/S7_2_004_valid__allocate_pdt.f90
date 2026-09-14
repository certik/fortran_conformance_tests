! rule: S7.2-004
! covers: allocate-pdt
! evidence: effect
program type_parameters_deferred_allocate_pdt
    implicit none
    integer, parameter :: family = kind(0)
    type :: packet(k, n)
        integer, kind :: k
        integer, len :: n
        integer :: payload(n)
    end type packet
    type(packet(family, :)), allocatable :: value
    integer :: status

    allocate(packet(family, 3) :: value, stat=status)
    if (status /= 0) error stop 1
    if (.not. allocated(value)) error stop 2
    if (value%k /= family) error stop 3
    if (kind(value%n) /= kind(0)) error stop 4
    if (value%n /= 3) error stop 5
    if (size(value%payload) /= 3) error stop 6
    if (lbound(value%payload, 1) /= 1) error stop 7
    value%payload(:) = [7, 11, 13]
    if (any(value%payload /= [7, 11, 13])) error stop 8
end program type_parameters_deferred_allocate_pdt
