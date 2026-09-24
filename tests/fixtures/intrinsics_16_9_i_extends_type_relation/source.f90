program i169i_extends_type_relation
  implicit none
  type :: parent
    integer :: p = 1
  end type parent
  type, extends(parent) :: child
    integer :: c = 2
  end type child
  type, extends(child) :: grandchild
    integer :: g = 3
  end type grandchild
  type, extends(parent) :: sibling
    integer :: s = 4
  end type sibling
  type(parent) :: p
  type(child) :: c
  type(grandchild) :: g
  type(sibling) :: s
  logical :: inquiry_result
  call require_true('dynamic type extension inquiry child parent', extends_type_of(c, p))
  inquiry_result = .false.
  inquiry_result = extends_type_of(g, p)
  call require_true('inquiry function usable in logical expression', inquiry_result)
  call require_true('grandchild extends parent true iff', extends_type_of(g, p))
  call require_false('parent does not extend child true iff', extends_type_of(p, c))
  call require_false('sibling does not extend child true iff', extends_type_of(s, c))
  write(*,'(a)') 'INTRINSICS 16.9.I EXTENDS TYPE RELATION OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
end program i169i_extends_type_relation
