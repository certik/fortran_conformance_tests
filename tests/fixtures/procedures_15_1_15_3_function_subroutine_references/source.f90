! rule: S15.2.1-001
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
module function_subroutine_references_m
  implicit none
  integer :: finalized = -1
  type :: box
    integer :: value
  contains
    procedure :: write_formatted
    generic :: write(formatted) => write_formatted
    final :: finalize_box
  end type
  interface operator(.plusone.)
    module procedure plusone
  end interface
  interface assignment(=)
    module procedure assign_box
  end interface
contains
  integer function answer()
    answer = 42
  end function
  integer function plusone(x)
    integer, intent(in) :: x
    plusone = x + 1
  end function
  subroutine set_answer(x)
    integer, intent(out) :: x
    x = 42
  end subroutine
  subroutine leave_sentinel(x)
    integer, intent(inout) :: x
    x = x
  end subroutine
  subroutine assign_box(lhs, rhs)
    type(box), intent(out) :: lhs
    integer, intent(in) :: rhs
    lhs%value = rhs + 21
  end subroutine
  subroutine write_formatted(dtv, unit, iotype, v_list, iostat, iomsg)
    class(box), intent(in) :: dtv
    integer, intent(in) :: unit
    character(len=*), intent(in) :: iotype
    integer, intent(in) :: v_list(:)
    integer, intent(out) :: iostat
    character(len=*), intent(inout) :: iomsg
    write(unit,'(a,i0)') 'DEFINED_IO:', dtv%value
    iostat = 0
  end subroutine
  subroutine finalize_box(item)
    type(box), intent(inout) :: item
    finalized = item%value
  end subroutine
end module
program function_subroutine_references
  use function_subroutine_references_m
  implicit none
  integer :: value, unit
  character(len=32) :: line
  type(box) :: assigned
  value = -100
  value = answer()
  if (value /= 42) error stop 1
  value = -101
  value = .plusone. 41
  if (value /= 42) error stop 2
  value = -102
  call set_answer(value)
  if (value /= 42) error stop 3
  assigned%value = -7
  assigned = 21
  if (assigned%value /= 42) error stop 4
  open(newunit=unit, file='defined_io_record.txt', status='replace', action='readwrite')
  write(unit,'(dt)') assigned
  rewind(unit)
  line = '################################'
  read(unit,'(a)') line
  close(unit, status='delete')
  if (len_trim(line) /= 13) error stop 5
  if (line(:13) /= 'DEFINED_IO:42') error stop 6
  block
    type(box) :: local
    local%value = 42
  end block
  if (finalized /= 42) error stop 7
  print '(a)', 'PROCEDURES 15.2.1 FUNCTION SUBROUTINE REFERENCES OK'
end program
