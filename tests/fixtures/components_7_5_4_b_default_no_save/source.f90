program component_default_no_save
implicit none
type :: record
  integer :: value = 7
end type
call visit(1)
call visit(2)
print '(a)', 'COMPONENTS 7.5.4B NO SAVE OK'
contains
subroutine visit(iteration)
  integer, intent(in) :: iteration
  type(record) :: automatic
  type(record), save :: persistent
  if (automatic%value /= 7) error stop 1
  if (iteration == 1) then
    if (persistent%value /= 7) error stop 2
  else
    if (persistent%value /= 99) error stop 3
  end if
  automatic%value = 99
  persistent%value = 99
end subroutine
end program
