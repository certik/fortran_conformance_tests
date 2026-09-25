module procedure_reference_15_5_1_designator_m
  implicit none
  abstract interface
    subroutine set_iface(x)
      integer, intent(out) :: x
    end subroutine
  end interface
  type holder
    procedure(set_iface), pointer, nopass :: op => null()
  end type
  type tagged
    integer :: value = -3
  contains
    procedure :: tb_set
    procedure :: tb_set_other
  end type
contains
  subroutine named_set(x)
    integer, intent(out) :: x
    x = 101
  end subroutine
  subroutine named_set_other(x)
    integer, intent(out) :: x
    x = 111
  end subroutine
  subroutine comp_set(x)
    integer, intent(out) :: x
    x = 202
  end subroutine
  subroutine comp_set_other(x)
    integer, intent(out) :: x
    x = 212
  end subroutine
  subroutine tb_set(self)
    class(tagged), intent(inout) :: self
    self%value = 303
  end subroutine
  subroutine tb_set_other(self)
    class(tagged), intent(inout) :: self
    self%value = 313
  end subroutine
end module procedure_reference_15_5_1_designator_m

program procedure_reference_15_5_1_designator
  use procedure_reference_15_5_1_designator_m
  implicit none
  type(holder) :: h
  type(tagged) :: obj
  integer :: named, component, checks
  checks = 0
  named = -4
  call named_set(named)
  if (named /= 101) error stop 301
  checks = checks + 1
  component = -5
  h%op => comp_set
  call h%op(component)
  if (component /= 202) error stop 302
  checks = checks + 1
  obj%value = -3
  call obj%tb_set()
  if (obj%value /= 303) error stop 303
  checks = checks + 1
  if (checks /= 3) error stop 399
  print '(a)', 'PROCEDURE REFERENCE DESIGNATORS OK'
end program procedure_reference_15_5_1_designator
