! rule: S10.2.1.3-007
! covers: parameterized-derived-kind
! profile: two-integer-kinds
! F2023 10.2.1.3 p3, bullet 1. KIND parameters are selected by the type guards.
program s10_2_1_3_007_pdt
    use iso_fortran_env, only: integer_kinds
    implicit none
    integer, parameter :: normal = kind(0)
    integer, parameter :: other = maxval(integer_kinds, mask=integer_kinds /= normal)
    type :: box(k)
        integer, kind :: k
        integer(k) :: value
    end type
    type(box(normal)) :: a
    type(box(other)) :: b
    class(*), allocatable :: copy
    a%value = 17
    b%value = 29_other
    copy = a
    if (.not. allocated(copy)) error stop 'pdt-allocation'
    select type (copy)
    type is (box(normal))
        if (copy%k /= normal .or. copy%value /= 17) error stop 'normal-kind-value'
    class default
        error stop 'normal-kind'
    end select
    copy = b
    select type (copy)
    type is (box(other))
        if (copy%k /= other .or. copy%value /= 29_other) error stop 'other-kind-value'
    class default
        error stop 'other-kind'
    end select
end program
