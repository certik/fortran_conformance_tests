! rule: S7.4.4.2-006
! covers: allocate-effective-lengths
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    character(2), allocatable :: short
    character(5), allocatable :: long
    call establish(short, long)
    if (.not. allocated(short)) error stop 1
    if (.not. allocated(long)) error stop 2
    if (len(short) /= 2 .or. len(long) /= 5) error stop 3
    if (short /= 'AB' .or. long /= 'CDEFG') error stop 4
    deallocate(short, long)
contains
    subroutine establish(a, b)
        character(*), allocatable, intent(inout) :: a, b
        integer :: stat
        allocate(character(*) :: a, b, stat=stat)
        if (stat /= 0) error stop 5
        if (.not. allocated(a)) error stop 6
        if (.not. allocated(b)) error stop 7
        if (len(a) /= 2 .or. len(b) /= 5) error stop 8
        a = 'AB'
        b = 'CDEFG'
    end subroutine
end program
