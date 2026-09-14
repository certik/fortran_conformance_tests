! rule: S7.1.2-001
! covers: local-derived-name
! evidence: positive-control
program type_basics_local
    implicit none
    type :: item
        integer :: payload
    end type item
    type(item) :: value

    value%payload = 17
    if (value%payload /= 17) error stop 1
end program type_basics_local
