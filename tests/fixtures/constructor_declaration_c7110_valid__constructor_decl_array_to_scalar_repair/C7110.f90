module constructor_types
implicit none
type :: holder
integer, pointer :: one=>null()
integer, pointer :: many(:)=>null()
end type holder
end module constructor_types
program constructor_case
use constructor_types
implicit none
type(holder) :: value
integer, target :: scalar_target,vec(2)
integer, pointer :: scalar_mold=>null()
integer, pointer :: array_mold(:)=>null()
scalar_target=17
vec(1)=11
vec(2)=13
value=holder(one=scalar_target,many=vec)
value=holder(one=vec(1),many=vec(1:2))
value=holder(one=null(),many=null())
value=holder(one=null(mold=scalar_mold),many=null(mold=array_mold))
value=holder(one=vec(1))
end program constructor_case
