program c709_typeof_prefix
    implicit none
    integer :: seed = 3
    if (make() /= 7) error stop 'result'
contains
    typeof(seed) function make() result(value)
        value = 7
    end function
end program
