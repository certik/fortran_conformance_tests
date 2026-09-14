program c709_classof_prefix
    implicit none
    type :: payload
        integer :: code
    end type
    type(payload) :: seed = payload(3)
    class(payload), allocatable :: object
    object = make()
    if (.not. allocated(object)) error stop 'allocation'
    if (object%code /= 7) error stop 'result'
contains
    classof(seed) function make() result(value)
        allocatable :: value
        allocate(payload :: value)
        if (.not. allocated(value)) error stop 'result-allocation'
        value%code = 7
    end function
end program
