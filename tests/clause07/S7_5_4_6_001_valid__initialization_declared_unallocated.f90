! rule: S7.5.4.6-001
! covers: declared-object-status nested-container-status
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
type(record) :: item
if (allocated(item%values)) error stop 1
if (allocated(item%nested%scalar)) error stop 2
if (allocated(item%nested%values)) error stop 3
end program
