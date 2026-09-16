! rule: S7.5.4.6-001
! covers: allocated-container-status
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: inner
integer, allocatable :: scalar, values(:)
end type
type :: record
type(inner) :: nested
integer, allocatable :: values(:)
end type
type(record), allocatable :: item
integer :: stat
allocate(item,stat=stat)
if (stat /= 0) error stop 10
if (.not.allocated(item)) error stop 12
if (allocated(item%values)) error stop 1
if (allocated(item%nested%scalar)) error stop 2
if (allocated(item%nested%values)) error stop 3
deallocate(item,stat=stat)
if (stat /= 0) error stop 11
end program
