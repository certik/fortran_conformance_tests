! rule: C712
! covers: enumeration-data-ref
! evidence: positive-control
! standard: f2023
program c712_enumeration
    implicit none
    enumeration type :: tone
        enumerator :: low, high
    end enumeration type
    type(tone) :: seed = low
    classof(seed), allocatable :: copy
end program
