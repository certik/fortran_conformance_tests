! rule: S15.5.2.4-002
! covers: polymorphic-dummy-associated-with-pointer-target nonpolymorphic-dummy-associated-with-declared-type-part
! evidence: effect
! standard: f2023
module association_effects_m
  implicit none
  type :: parent
    integer :: base = -1
  end type
  type, extends(parent) :: child
    integer :: ext = -2
  end type
contains
  subroutine take_class(x, out_base, out_ext)
    class(parent), intent(inout) :: x
    integer, intent(out) :: out_base, out_ext
    select type (x)
    type is (child)
      out_base = x%base
      out_ext = x%ext
      x%base = 55
    class default
      out_base = x%base
      out_ext = -777
    end select
  end subroutine
  subroutine take_parent(x, out_base)
    type(parent), intent(inout) :: x
    integer, intent(out) :: out_base
    out_base = x%base
    x%base = 41
  end subroutine
  subroutine take_value(x, entry, local)
    integer, value :: x
    integer, intent(out) :: entry, local
    entry = x
    x = 29
    local = x
  end subroutine
  subroutine ptr_dummy(q)
    integer, pointer :: q
    integer, target, save :: second = 202
    q => second
  end subroutine
  subroutine outer(x)
    integer, intent(inout) :: x
    call inner(x)
  end subroutine
  subroutine inner(y)
    integer, intent(inout) :: y
    y = 83
  end subroutine
  subroutine outer_comp(obj)
    type(parent), intent(inout) :: obj
    call inner(obj%base)
  end subroutine
end module
program argument_association_effects
  use association_effects_m
  implicit none
  integer :: checks = 0
  integer, target :: target_value = 71, first = 101
  integer, pointer :: p, q
  logical :: inquiry = .true.
  integer :: base_seen = -5, ext_seen = -6
  type(child), target :: child_target
  class(parent), pointer :: class_pointer
  type(parent), pointer :: parent_pointer
  type(child) :: child_actual
  integer :: caller_value = 17, entry_seen = -1, local_seen = -2
  integer :: ultimate = -83
  type(parent) :: holder, sibling
  p => target_value
  call read_nonpointer(p, base_seen)
  call expect_equal(base_seen, 71, 'associated pointer actual')
  nullify(p)
  inquiry = associated(p)
  call expect_false(inquiry, 'intrinsic inquiry exception')
  child_target%base = 23; child_target%ext = 5; class_pointer => child_target
  call take_class(class_pointer, base_seen, ext_seen)
  call expect_equal(base_seen, 23, 'polymorphic pointer target base')
  call expect_equal(ext_seen, 5, 'polymorphic pointer target extension')
  child_target%base = 23; child_target%ext = 99; parent_pointer => child_target%parent
  call take_parent(parent_pointer, base_seen)
  call expect_equal(base_seen, 23, 'nonpolymorphic pointer declared part entry')
  call expect_equal(child_target%base, 41, 'nonpolymorphic pointer declared part update')
  call expect_equal(child_target%ext, 99, 'extension component not associated')
  child_actual%base = 7; child_actual%ext = 31
  call take_class(child_actual, base_seen, ext_seen)
  call expect_equal(ext_seen, 31, 'polymorphic nonpointer actual')
  child_actual%base = 7; child_actual%ext = 99
  call take_parent(child_actual%parent, base_seen)
  call expect_equal(base_seen, 7, 'nonpolymorphic nonpointer declared part entry')
  call expect_equal(child_actual%base, 41, 'nonpolymorphic nonpointer declared part update')
  call expect_equal(child_actual%ext, 99, 'nonpolymorphic nonpointer extension unchanged')
  caller_value = 17
  call take_value(caller_value, entry_seen, local_seen)
  call expect_equal(entry_seen, 17, 'value dummy initial value')
  call expect_equal(local_seen, 29, 'value dummy definable local')
  call expect_equal(caller_value, 17, 'value dummy caller unchanged')
  q => first
  call ptr_dummy(q)
  call expect_true(associated(q), 'pointer dummy actual associated')
  call expect_false(associated(q, first), 'pointer dummy actual retargeted')
  call expect_equal(q, 202, 'pointer dummy target value')
  ultimate = -83
  call outer(ultimate)
  call expect_equal(ultimate, 83, 'ultimate dummy chain')
  holder%base = -97; sibling%base = -96
  call outer_comp(holder)
  call expect_equal(holder%base, 83, 'ultimate subobject chain')
  call expect_equal(sibling%base, -96, 'ultimate sibling unchanged')
  call expect_equal(checks, 20, 'check count')
  write(*,'(a)') 'ARGUMENT ASSOCIATION EFFECTS OK'
contains
  subroutine read_nonpointer(x, out)
    integer, intent(in) :: x
    integer, intent(out) :: out
    out = x
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
  subroutine expect_true(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (.not. got) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_false(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (got) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
