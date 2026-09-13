! rule: S10.2.1.3-007
! covers: extension-type unlimited-polymorphic-intrinsic changed-dynamic-type
! F2023 10.2.1.3 p3, bullet 1.
program s10_2_1_3_007_valid
    implicit none
    integer, parameter :: sp = kind(0.0), dp = kind(0.0d0)
    type :: base
        integer :: x
    end type
    type, extends(base) :: child
        integer :: y
    end type
    type(base) :: b
    type(child) :: c
    class(base), allocatable :: object
    class(*), allocatable :: number
    b%x = 17
    c%x = 23
    c%y = 31
    object = b
    if (.not. allocated(object)) error stop 'base-allocation'
    select type (object)
    type is (base)
        if (object%x /= 17) error stop 'base-value'
    class default
        error stop 'base-type'
    end select
    object = c
    select type (object)
    type is (child)
        if (object%x /= 23 .or. object%y /= 31) error stop 'extension-value'
    class default
        error stop 'extension-type'
    end select
    object = b
    select type (object)
    type is (base)
        if (object%x /= 17) error stop 'changed-type-value'
    class default
        error stop 'changed-dynamic-type'
    end select
    number = 1.5_dp
    if (.not. allocated(number)) error stop 'intrinsic-allocation'
    select type (number)
    type is (real(kind=dp))
        if (number /= 1.5_dp) error stop 'double-value'
    class default
        error stop 'double-kind'
    end select
    number = 2.5_sp
    select type (number)
    type is (real(kind=sp))
        if (number /= 2.5_sp) error stop 'default-real-value'
    class default
        error stop 'default-real-kind'
    end select
end program
