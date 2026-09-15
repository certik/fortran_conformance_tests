! rule: S7.4.4.2-006
! covers: allocatable-assumed-dummy
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    character(3), allocatable :: text
    integer :: stat
    allocate(text, stat=stat)
    if (stat /= 0) error stop 1
    text = 'ABC'
    call check(text)
contains
    subroutine check(value)
        character(*), allocatable, intent(in) :: value
        if (.not. allocated(value)) error stop 2
        if (len(value) /= 3) error stop 3
        if (value /= 'ABC') error stop 4
    end subroutine
end program
