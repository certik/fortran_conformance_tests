! rule: S15.5.2.2-001
! covers: type-bound-data-ref-passed-object procedure-pointer-component-data-ref-passed-object
! evidence: effect
! standard: f2023
module argument_correspondence_objects
  implicit none
  type :: box
    integer :: slot = -9
    procedure(set_iface), pointer, pass(self) :: pp => null()
  contains
    procedure :: set => set_box
  end type
  abstract interface
    subroutine set_iface(self, value)
      import :: box
      class(box), intent(inout) :: self
      integer, intent(in) :: value
    end subroutine
  end interface
contains
  subroutine set_box(self, value)
    class(box), intent(inout) :: self
    integer, intent(in) :: value
    self%slot = value
  end subroutine
end module
program argument_correspondence_passed_object
  use argument_correspondence_objects
  implicit none
  integer :: checks = 0
  integer :: key_a = -71, key_b = -72, pos_a = -81, pos_b = -82
  type(box) :: reduced, type_bound, proc_ptr, untouched, pp_other
  call record_pair(b=17, a=11, out_a=key_a, out_b=key_b)
  call expect_equal(key_a, 11, 'keyword dummy a')
  call expect_equal(key_b, 17, 'keyword dummy b')
  call record_pair(23, 29, pos_a, pos_b)
  call expect_equal(pos_a, 23, 'positional dummy a')
  call expect_equal(pos_b, 29, 'positional dummy b')
  call reduced%set(41)
  call expect_equal(reduced%slot, 41, 'reduced list passed object')
  call expect_equal(untouched%slot, -9, 'untouched reduced peer')
  call type_bound%set(47)
  call expect_equal(type_bound%slot, 47, 'type-bound data-ref object')
  proc_ptr%pp => set_box
  pp_other%pp => set_box
  call proc_ptr%pp(43)
  call expect_equal(proc_ptr%slot, 43, 'procedure pointer component object')
  call expect_equal(checks, 8, 'check count')
  write(*,'(a)') 'ARGUMENT CORRESPONDENCE PASSED OBJECT OK'
contains
  subroutine record_pair(a, b, out_a, out_b)
    integer, intent(in) :: a, b
    integer, intent(out) :: out_a, out_b
    out_a = a
    out_b = b
  end subroutine
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'AA1552-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
