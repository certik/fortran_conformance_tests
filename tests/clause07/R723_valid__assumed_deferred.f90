! rule: R723
! covers: assumed-and-deferred-values
! evidence: positive-control
! standard: f2023
program character_type_case
    implicit none
    character, allocatable :: allocated_text*(:)
    character, pointer :: pointed_text*(:)
    character(3), target :: target
    integer :: stat
    target = 'xyz'
    call assumed('ABC')
    allocate(character(3) :: allocated_text, stat=stat)
    if (stat /= 0) error stop 1
    if (.not. allocated(allocated_text)) error stop 2
    allocated_text = 'ABC'
    pointed_text => target
    if (.not. associated(pointed_text)) error stop 3
    if (len(allocated_text) /= 3 .or. len(pointed_text) /= 3) error stop 4
    if (allocated_text /= 'ABC' .or. pointed_text /= 'xyz') error stop 5
contains
    subroutine assumed(text)
        character, intent(in) :: text*(*)
        if (len(text) /= 3 .or. text /= 'ABC') error stop 6
    end subroutine
end program
