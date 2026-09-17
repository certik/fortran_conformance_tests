

























module c815_public_twice
    implicit none
    integer, public :: m = 1
       ! {error C815 access-stmt}
end module
