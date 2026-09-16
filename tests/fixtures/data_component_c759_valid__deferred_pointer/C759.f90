program p
implicit none
type :: record
    character(:), pointer :: field
end type
type(record) :: value
character(3), target :: target
target = 'ABC'
nullify(value%field)
if (associated(value%field)) error stop 1
value%field => target
if (.not. associated(value%field)) error stop 2
if (len(value%field) /= 3 .or. value%field /= 'ABC') error stop 3
value%field = 'DEF'
if (target /= 'DEF') error stop 4
nullify(value%field)
end program
