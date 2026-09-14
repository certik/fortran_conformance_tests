program scalar_condition
    implicit none
    logical :: condition(1)
    integer :: result
    condition = .true.
    result = 0
    if (condition(1)) result = 1
    if (result /= 1) stop 1
end program scalar_condition
