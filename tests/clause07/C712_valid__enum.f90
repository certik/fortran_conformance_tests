! rule: C712
! covers: enum-data-ref
! evidence: positive-control
! standard: f2023
program c712_enum
    implicit none
    enum, bind(c) :: tone
        enumerator :: low = 2, high = 5
    end enum
    type(tone) :: seed = low
    classof(seed), allocatable :: copy
end program
